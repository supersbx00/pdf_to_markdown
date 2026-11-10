from app.main import mcp


def test_mcp_expone_solo_convertir_pdf_a_md():
    assert [t.name for t in mcp.tools] == ["convertir_pdf_a_md"]
