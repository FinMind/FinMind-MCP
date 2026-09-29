"""Tests for the knowledge-pack loader, focused on dataset_catalog parsing."""

from finmind_mcp import knowledge


def test_dataset_catalog_parses_datasets_md():
    catalog = knowledge.dataset_catalog()
    # The shipped datasets.md lists ~90 datasets.
    assert len(catalog) >= 80
    names = {rec["name"] for rec in catalog}
    assert "TaiwanStockPrice" in names
    assert "TaiwanStockInfo" in names
    # Every record carries the expected keys.
    for rec in catalog:
        assert set(rec) == {"name", "category", "tier", "desc"}
        assert rec["name"]
        assert rec["category"]  # each dataset sits under a "## " section


def test_dataset_catalog_captures_tier_and_category():
    by_name = {rec["name"]: rec for rec in knowledge.dataset_catalog()}
    price = by_name["TaiwanStockPrice"]
    assert "Free" in price["tier"]
    # Legend section "Tier 說明" must never produce a dataset record.
    assert "Tier 說明" not in {rec["category"] for rec in by_name.values()}


def test_pricing_resource_is_registered_and_readable():
    uris = [str(r.uri) for r in knowledge.resource_definitions()]
    assert "finmind://pricing" in uris
    md = knowledge.read("finmind://pricing")
    assert "Sponsor Pro" in md
    assert "https://finmindtrade.com/analysis/#/Sponsor/sponsor" in md


def test_no_dead_upgrade_link_in_knowledge_pack():
    # /account/pricing is not a real route on finmindtrade.com.
    for r in knowledge.resource_definitions():
        assert "#/account/pricing" not in knowledge.read(str(r.uri))
