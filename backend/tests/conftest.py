import pytest

from app.core.rate_limit import reset_rate_limits


@pytest.fixture(autouse=True)
def _reset_password_attempts():
    """Bộ đếm nhập sai mật khẩu dùng chung cả tiến trình; xóa trước và sau mỗi test để test không ảnh hưởng nhau."""

    reset_rate_limits()
    yield
    reset_rate_limits()
