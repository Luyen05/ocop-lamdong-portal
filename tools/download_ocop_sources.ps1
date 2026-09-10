param(
    [string]$RepositoryRoot = (Split-Path -Parent $PSScriptRoot)
)

$ErrorActionPreference = "Stop"

$sources = @(
    @{
        Year = "2025"
        File = "202-2025-QH15.pdf"
        Url = "https://datafiles.chinhphu.vn/cpp/files/vbpq/2025/6/202qh.signed.pdf"
    },
    @{
        Year = "2025"
        File = "1671-NQ-UBTVQH15.pdf"
        Url = "https://moha.gov.vn/Upload/KND/vb/vbqp/Lists/VBQP/Attachments/478/77202516752L%C3%A2m%20%C4%90%E1%BB%93ng_0001.pdf"
    },
    @{
        Year = "2025"
        File = "1489-QD-TTg.pdf"
        Url = "https://datafiles.chinhphu.vn/cpp/files/vbpq/2025/7/1489-ttg.signed.pdf"
    },
    @{
        Year = "2025"
        File = "643-QD-UBND.pdf"
        Url = "https://ocoplamdong.gov.vn/Media/admin/files/Q%C4%90%20643%20UBND.pdf"
    },
    @{
        Year = "2025"
        File = "1253-QD-UBND.pdf"
        Url = "https://ocoplamdong.gov.vn/Media/admin/files/QD%201253.pdf"
    },
    @{
        Year = "2025"
        File = "858-QD-UBND-Dak-Nong.pdf"
        Url = "https://ocoplamdong.gov.vn/Media/admin/files/Q%C4%90%20c%C3%B4ng%20nh%E1%BA%ADn%204%20sao%202025.pdf"
    },
    @{
        Year = "2025"
        File = "Dak-Song-OCOP-2025.pdf"
        Url = "https://ocoplamdong.gov.vn/Media/admin/files/DakSong%202025.pdf"
    },
    @{
        Year = "2025"
        File = "Cu-Jut-OCOP-2025.pdf"
        Url = "https://ocoplamdong.gov.vn/Media/admin/files/Cu%20Jut.pdf"
    },
    @{
        Year = "2026"
        File = "26-2026-QD-TTg.pdf"
        Url = "https://datafiles.chinhphu.vn/cpp/files/vbpq/2026/5/26-ttg-2026.signed.pdf"
    },
    @{
        Year = "2026"
        File = "3981-QD-UBND.pdf"
        Url = "https://ocoplamdong.gov.vn/Media/admin/files/225%20Quye%CC%82%CC%81t%20%C4%91i%CC%A3nh%20Q%C4%90%20cu%CC%89a%20UBND%20ti%CC%89nh_signed%281%29.pdf"
    }
)

foreach ($source in $sources) {
    $directory = Join-Path $RepositoryRoot ("docs\sources\ocop\" + $source.Year)
    $destination = Join-Path $directory $source.File
    New-Item -ItemType Directory -Force -Path $directory | Out-Null

    if (Test-Path -LiteralPath $destination) {
        Write-Host "Da ton tai: $destination"
        continue
    }

    Write-Host "Dang tai: $($source.Url)"
    Invoke-WebRequest -Uri $source.Url -OutFile $destination -UseBasicParsing
}

Write-Host "Hoan tat tai nguon PDF."
