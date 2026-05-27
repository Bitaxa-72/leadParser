param(
    [int]$Limit = 50
)

python -m promotion_collector.cli collect-group --group russia-million-plus --limit $Limit --sources overpass --no-enrich-websites
