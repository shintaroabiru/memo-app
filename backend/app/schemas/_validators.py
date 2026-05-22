"""Pydantic スキーマ間で共有するバリデーションヘルパー。

`requirements.md` §2.0 の共通バリデーション規則（文字列の前後空白トリム）の
実装ポイントを 1 箇所に集約する。新規スキーマで文字列フィールドを追加するときは、
本モジュールの `strip_str` を `BeforeValidator` に渡して長さ制約と合成すること。

実装例:

```python
from typing import Annotated
from pydantic import BeforeValidator, Field
from app.schemas._validators import strip_str

DisplayName = Annotated[
    str,
    BeforeValidator(strip_str),
    Field(min_length=1, max_length=50),
]
```
"""

from __future__ import annotations


def strip_str(value: object) -> object:
    """文字列なら前後空白をトリム。`min_length=1` と組み合わせれば空白のみを弾ける。

    `BeforeValidator` 経由で長さ制約より前に評価されることを前提とする。
    `str` 以外の値（None / 数値など）はそのまま返し、後段の型バリデーションに委ねる。
    """
    return value.strip() if isinstance(value, str) else value


def strip_or_none(value: object) -> object:
    """文字列なら strip し、空文字列になったら `None` に正規化する。

    `bio` / `avatar_url` のような **任意の文字列フィールド** で
    「未指定 (None)」「空文字列」を 1 つの状態 (None) にまとめるために使う。
    フィールド型は `str | None` を期待し、`BeforeValidator` 経由で適用する。
    """
    if not isinstance(value, str):
        return value
    stripped = value.strip()
    return stripped if stripped else None
