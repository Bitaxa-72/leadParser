param(
    [string]$City = "nha-trang",
    [int]$Limit = 10
)

python -m promotion_collector.cli collect --city $City --limit $Limit
