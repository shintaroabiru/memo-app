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

from pydantic_core import PydanticCustomError


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


def normalize_body(value: object) -> object:
    """本文系の長文フィールドを正規化する。

    - 末尾の空白・改行のみトリム (`rstrip()`)。先頭・中間は意図 (インデント等)
      を尊重して保存する
    - PostgreSQL の `TEXT` が拒否する NULL バイト (`\\x00`) を含む入力は
      `null_byte_in_body` として `PydanticCustomError` を投げ、共通ハンドラで
      400 `VALIDATION_ERROR` にする（DB の `DataError` を 500 として晒さない）
    - トリム後に空文字列になった場合は `None` に正規化する
      （`strip_or_none` と同じく「未指定」を単一状態に揃える）
    - TAB / LF / CR を含むその他の制御文字は通常の入力として許容する

    `memo.body` のような **任意の長文フィールド** で使う想定。
    フィールド型は `str | None` を期待し、`BeforeValidator` 経由で適用する。
    """
    if value is None:
        return None
    if not isinstance(value, str):
        return value
    if "\x00" in value:
        raise PydanticCustomError(
            "null_byte_in_body",
            "本文に NULL バイトを含めることはできません",
        )
    stripped = value.rstrip()
    return stripped if stripped else None
