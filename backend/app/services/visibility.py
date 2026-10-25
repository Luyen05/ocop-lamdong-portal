"""Điều kiện hiển thị công khai theo tài khoản của chủ thể."""

from sqlalchemy import or_

from app.models.user import User

# Tài khoản kỹ thuật do seed tạo cho chủ thể nhập từ nguồn công khai (đuôi .invalid dành riêng theo
# RFC 2606, không ai đăng ký được). Các tài khoản này luôn ở trạng thái khóa để không đăng nhập được,
# nhưng sản phẩm, điểm du lịch của chúng vẫn phải hiển thị.
REFERENCE_ACCOUNT_EMAIL_SUFFIX = "@local.invalid"


def account_allows_public_content():
    """Tài khoản còn hoạt động, hoặc là tài khoản dữ liệu nguồn công khai.

    Admin khóa tài khoản của chủ thể thì sản phẩm, điểm du lịch của chủ thể ngừng hiển thị công khai.
    """

    return or_(User.is_active.is_(True), User.email.like(f"%{REFERENCE_ACCOUNT_EMAIL_SUFFIX}"))
