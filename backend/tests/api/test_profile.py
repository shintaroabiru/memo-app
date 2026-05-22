"""プロフィールAPIのテスト。"""

from fastapi.testclient import TestClient

from app.models import UserProfile


def test_get_profile_returns_200_with_default_user(
    api_client: TestClient, default_user: UserProfile
) -> None:
    res = api_client.get("/api/v1/profile")

    assert res.status_code == 200
    body = res.json()
    assert body["id"] == str(default_user.id)
    assert body["display_name"] == default_user.display_name
    assert {"id", "display_name", "bio", "avatar_url", "created_at", "updated_at"} <= body.keys()


def test_put_profile_updates_fields(api_client: TestClient) -> None:
    res = api_client.put(
        "/api/v1/profile",
        json={
            "display_name": "  しん  ",  # トリムされて "しん"
            "bio": "  AIエンジニア  ",
            "avatar_url": "https://example.com/a.png",
        },
    )

    assert res.status_code == 200
    body = res.json()
    assert body["display_name"] == "しん"
    assert body["bio"] == "AIエンジニア"
    assert body["avatar_url"] == "https://example.com/a.png"


def test_put_profile_persists_across_get(api_client: TestClient) -> None:
    api_client.put("/api/v1/profile", json={"display_name": "更新後", "bio": "新しい自己紹介"})

    res = api_client.get("/api/v1/profile")
    body = res.json()
    assert body["display_name"] == "更新後"
    assert body["bio"] == "新しい自己紹介"


def test_put_profile_can_clear_bio_to_null(api_client: TestClient) -> None:
    api_client.put("/api/v1/profile", json={"display_name": "x", "bio": "古い"})

    res = api_client.put("/api/v1/profile", json={"display_name": "x"})  # bio 省略

    assert res.status_code == 200
    assert res.json()["bio"] is None


def test_put_profile_returns_400_for_empty_display_name(api_client: TestClient) -> None:
    res = api_client.put("/api/v1/profile", json={"display_name": ""})

    assert res.status_code == 400
    assert res.json()["error"]["code"] == "VALIDATION_ERROR"


def test_put_profile_returns_400_for_whitespace_only_display_name(api_client: TestClient) -> None:
    res = api_client.put("/api/v1/profile", json={"display_name": "   "})

    assert res.status_code == 400


def test_put_profile_returns_400_when_display_name_too_long(api_client: TestClient) -> None:
    res = api_client.put("/api/v1/profile", json={"display_name": "a" * 51})

    assert res.status_code == 400


def test_put_profile_returns_400_when_bio_too_long(api_client: TestClient) -> None:
    res = api_client.put("/api/v1/profile", json={"display_name": "x", "bio": "a" * 201})

    assert res.status_code == 400


def test_put_profile_normalizes_empty_bio_to_null(api_client: TestClient) -> None:
    res = api_client.put("/api/v1/profile", json={"display_name": "x", "bio": ""})

    assert res.status_code == 200
    assert res.json()["bio"] is None


def test_put_profile_normalizes_empty_avatar_url_to_null(api_client: TestClient) -> None:
    res = api_client.put(
        "/api/v1/profile", json={"display_name": "x", "avatar_url": ""}
    )

    assert res.status_code == 200
    assert res.json()["avatar_url"] is None
