from types import SimpleNamespace
import unittest
from unittest.mock import patch

import pandas as pd

from akshare.fund import fund_em


class FundInfoActionsTests(unittest.TestCase):
    def test_actions_skip_nav_request_and_parse_once(self):
        dividends = pd.DataFrame([["分红", "2026-01-01"]])
        splits = pd.DataFrame([["拆分", "2026-02-01"]])

        for extra_table in (False, True):
            for indicator in ("分红送配详情", "拆分详情", "分红拆分"):
                with self.subTest(extra_table=extra_table, indicator=indicator):
                    tables = [dividends, splits]
                    if extra_table:
                        tables.insert(0, pd.DataFrame([["说明", ""]]))
                    calls = []
                    parses = []

                    def fake_get(url, **kwargs):
                        calls.append(url)
                        return SimpleNamespace(text="<table></table>")

                    def fake_read_html(source):
                        parses.append(source.read())
                        return tables

                    with (
                        patch.object(fund_em.http, "get", fake_get),
                        patch.object(fund_em.pd, "read_html", fake_read_html),
                        patch.object(
                            fund_em.py_mini_racer,
                            "MiniRacer",
                            side_effect=AssertionError("unexpected JS engine"),
                        ),
                    ):
                        result = fund_em.fund_open_fund_info_em(
                            "000001", indicator=indicator
                        )

                    self.assertEqual(
                        calls, ["https://fundf10.eastmoney.com/fhsp_000001.html"]
                    )
                    self.assertEqual(parses, ["<table></table>"])
                    if indicator == "分红拆分":
                        pd.testing.assert_frame_equal(result[0], dividends)
                        pd.testing.assert_frame_equal(result[1], splits)
                    else:
                        pd.testing.assert_frame_equal(
                            result,
                            dividends if indicator == "分红送配详情" else splits,
                        )

    def test_empty_tables(self):
        tables = [
            pd.DataFrame([["分红", "暂无分红信息!"]]),
            pd.DataFrame([["拆分", "暂无拆分信息!"]]),
        ]
        with (
            patch.object(
                fund_em.http,
                "get",
                return_value=SimpleNamespace(text="empty"),
            ),
            patch.object(fund_em.pd, "read_html", return_value=tables),
            patch.object(
                fund_em.py_mini_racer,
                "MiniRacer",
                side_effect=AssertionError("unexpected JS engine"),
            ),
        ):
            dividends, splits = fund_em.fund_open_fund_info_em(
                "000001", indicator="分红拆分"
            )
        self.assertTrue(dividends.empty)
        self.assertTrue(splits.empty)


if __name__ == "__main__":
    unittest.main()
