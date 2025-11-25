"""
Cart API Views
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from bson import ObjectId
from bson.errors import InvalidId
from mongoengine.errors import ValidationError as MEValidationError

from users.auth import require_auth
from users.models import User
from products.models import Product, ChildCategory
from products.views import _pick_lang
from .models import Cart, ProductInCart, Voucher, UserVoucher
from datetime import datetime


def _get_or_create_cart(user):
    """Get or create cart for user"""
    cart = Cart.objects(user=user).first()
    if not cart:
        cart = Cart(user=user)
        cart.save()
    return cart


def _validate_size_color(product, size, color):
    """Validate size and color belong to product"""
    errors = []
    
    # Validate size
    if size:
        size_valid = False
        for size_variant in product.sizes:
            size_name = _pick_lang(size_variant.size_name, 'vi')
            if size_name and size_name == size:
                size_valid = True
                break
        if not size_valid:
            errors.append("Size không hợp lệ cho sản phẩm này")
    
    # Validate color
    if color:
        color_valid = False
        for color_variant in product.colors:
            color_name = _pick_lang(color_variant.color_name, 'vi')
            if color_name and color_name == color:
                color_valid = True
                break
        if not color_valid:
            errors.append("Màu không hợp lệ cho sản phẩm này")
    
    return errors


def _serialize_cart_item(item, include_product_details=False):
    """Serialize cart item to dict"""
    data = {
        "product_id": str(item.product_id),
        "quantity": item.quantity,
        "size": item.size,
        "color": item.color
    }
    
    if include_product_details:
        try:
            product = Product.objects(id=item.product_id).first()
            if product:
                # Reload references
                if product.brand:
                    product.brand.reload()
                if product.category:
                    product.category.reload()
                    if product.category.parent:
                        product.category.parent.reload()
                
                product_data = {
                    "_id": str(product.id),
                    "name": _pick_lang(product.name, 'vi') or "",
                    "originalPrice": int(product.original_price) if product.original_price else 0,
                    "sold": product.sold or 0,
                    "rate": product.rate or 0,
                    "stock": product.stock or 0,
                    "discount": int(product.discount) if product.discount else 0,
                    "description": _pick_lang(product.description, 'vi') or "",
                    "images": product.images or [],
                    "brand": {
                        "_id": str(product.brand.id),
                        "name": _pick_lang(product.brand.name, 'vi') or ""
                    } if product.brand else None,
                    "sizeTable": _pick_lang(product.size_table, 'vi') if product.size_table else None,
                    "category": {
                        "_id": str(product.category.id),
                        "name": _pick_lang(product.category.name, 'vi') or "",
                        "parent": {
                            "_id": str(product.category.parent.id),
                            "name": _pick_lang(product.category.parent.name, 'vi') or ""
                        } if product.category.parent else None
                    } if product.category else None,
                    "createdAt": product.created_at.isoformat() if product.created_at else None
                }
                data["product"] = product_data
        except Exception:
            pass  # If product not found, just skip product details
    
    return data


def _serialize_cart(cart, include_product_details=False):
    """Serialize cart to dict"""
    return {
        "_id": str(cart.id),
        "user": str(cart.user.id),
        "products": [_serialize_cart_item(item, include_product_details) for item in cart.products],
        "created_at": cart.created_at.isoformat() if cart.created_at else None,
        "updated_at": cart.updated_at.isoformat() if cart.updated_at else None
    }


class CartView(APIView):
    """GET /api/cart - Get cart"""
    
    @require_auth
    def get(self, request):
        try:
            user_id = request.user_claims['sub']
            user = User.objects(id=ObjectId(user_id)).first()
            
            if not user:
                return Response(
                    {"detail": "User not found"},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            cart = _get_or_create_cart(user)
            
            # Check if include product details
            include_details = request.query_params.get('include_details', 'false').lower() == 'true'
            
            response_data = _serialize_cart(cart, include_product_details=include_details)
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except InvalidId:
            return Response(
                {"detail": "Invalid user ID"},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {"detail": "Đã xảy ra lỗi khi lấy giỏ hàng"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CartItemAddView(APIView):
    """POST /api/cart/items - Add item to cart
       DELETE /api/cart/items - Clear all items from cart"""
    
    @require_auth
    def post(self, request):
        try:
            user_id = request.user_claims['sub']
            user = User.objects(id=ObjectId(user_id)).first()
            
            if not user:
                return Response(
                    {"detail": "User not found"},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Get request data
            product_id = request.data.get('productId')
            quantity = request.data.get('quantity')
            size = request.data.get('size')
            color = request.data.get('color')
            
            # Validate required fields
            if not product_id:
                return Response(
                    {"detail": "productId là bắt buộc"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if not quantity or not isinstance(quantity, int) or quantity < 1:
                return Response(
                    {"detail": "quantity phải là số nguyên dương"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if quantity > 99:
                return Response(
                    {"detail": "Số lượng tối đa là 99"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get product
            try:
                product = Product.objects(id=ObjectId(product_id), status="active").first()
            except (InvalidId, Exception):
                product = None
            
            if not product:
                return Response(
                    {"detail": "Sản phẩm không tồn tại hoặc đã bị xóa"},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Validate stock
            if product.stock <= 0:
                return Response(
                    {"detail": "Sản phẩm đã hết hàng"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Validate size and color
            validation_errors = _validate_size_color(product, size, color)
            if validation_errors:
                return Response(
                    {"detail": validation_errors[0]},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get or create cart
            cart = _get_or_create_cart(user)
            
            # Check cart limit (50 items)
            if len(cart.products) >= 50:
                # Check if item already exists
                existing_item = None
                for item in cart.products:
                    if (str(item.product_id) == str(product_id) and 
                        item.size == size and 
                        item.color == color):
                        existing_item = item
                        break
                
                if not existing_item:
                    return Response(
                        {"detail": "Giỏ hàng đã đạt giới hạn 50 sản phẩm"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            # Find existing item with same product, size, color
            existing_item = None
            for item in cart.products:
                if (str(item.product_id) == str(product_id) and 
                    item.size == size and 
                    item.color == color):
                    existing_item = item
                    break
            
            # Calculate new quantity
            if existing_item:
                new_quantity = existing_item.quantity + quantity
                if new_quantity > product.stock:
                    new_quantity = product.stock
                    message = "Đã cập nhật số lượng sản phẩm trong giỏ hàng (đã đạt giới hạn stock)"
                else:
                    message = "Đã cập nhật số lượng sản phẩm trong giỏ hàng"
                
                existing_item.quantity = new_quantity
                cart.save()
                
                response_data = {
                    "product_id": str(product_id),
                    "quantity": new_quantity,
                    "size": size,
                    "color": color,
                    "message": message
                }
                
                return Response(response_data, status=status.HTTP_200_OK)
            else:
                # Check stock before adding
                if quantity > product.stock:
                    quantity = product.stock
                
                # Create new item
                new_item = ProductInCart(
                    product_id=ObjectId(product_id),
                    quantity=quantity,
                    size=size,
                    color=color
                )
                
                cart.products.append(new_item)
                cart.save()
                
                response_data = {
                    "product_id": str(product_id),
                    "quantity": quantity,
                    "size": size,
                    "color": color,
                    "message": "Đã thêm sản phẩm vào giỏ hàng"
                }
                
                return Response(response_data, status=status.HTTP_201_CREATED)
            
        except InvalidId:
            return Response(
                {"detail": "Invalid product ID"},
                status=status.HTTP_400_BAD_REQUEST
            )
        except MEValidationError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
                return Response(
                    {"detail": "Đã xảy ra lỗi khi thêm sản phẩm vào giỏ hàng"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
    
    @require_auth
    def delete(self, request):
        """Clear all items from cart"""
        try:
            user_id = request.user_claims['sub']
            user = User.objects(id=ObjectId(user_id)).first()
            
            if not user:
                return Response(
                    {"detail": "User not found"},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            cart = Cart.objects(user=user).first()
            if cart:
                cart.products = []
                cart.save()
            
            return Response(
                {"message": "Đã xóa tất cả sản phẩm khỏi giỏ hàng"},
                status=status.HTTP_200_OK
            )
            
        except InvalidId:
            return Response(
                {"detail": "Invalid user ID"},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {"detail": "Đã xảy ra lỗi khi xóa giỏ hàng"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CartItemDetailView(APIView):
    """PUT /api/cart/items/:cartItemId - Update item quantity
       DELETE /api/cart/items/:cartItemId - Remove item from cart"""
    
    @require_auth
    def put(self, request, cartItemId):
        """Update item quantity"""
        try:
            user_id = request.user_claims['sub']
            user = User.objects(id=ObjectId(user_id)).first()
            
            if not user:
                return Response(
                    {"detail": "User not found"},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Get cart
            cart = Cart.objects(user=user).first()
            if not cart:
                return Response(
                    {"detail": "Không tìm thấy sản phẩm trong giỏ hàng"},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Parse cartItemId as index
            try:
                item_index = int(cartItemId)
            except ValueError:
                return Response(
                    {"detail": "Invalid cart item ID"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Validate index
            if item_index < 0 or item_index >= len(cart.products):
                return Response(
                    {"detail": "Không tìm thấy sản phẩm trong giỏ hàng"},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Get item
            item = cart.products[item_index]
            
            # Get new quantity
            quantity = request.data.get('quantity')
            if not quantity or not isinstance(quantity, int) or quantity < 1:
                return Response(
                    {"detail": "quantity phải là số nguyên dương"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if quantity > 99:
                return Response(
                    {"detail": "Số lượng tối đa là 99"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get product to check stock
            product = Product.objects(id=item.product_id).first()
            if not product:
                return Response(
                    {"detail": "Sản phẩm không tồn tại"},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Check stock
            if quantity > product.stock:
                quantity = product.stock
                if quantity == 0:
                    return Response(
                        {"detail": "Sản phẩm đã hết hàng"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            # Update quantity
            item.quantity = quantity
            cart.save()
            
            response_data = {
                "product_id": str(item.product_id),
                "quantity": quantity,
                "size": item.size,
                "color": item.color,
                "message": "Đã cập nhật số lượng thành công"
            }
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except InvalidId:
            return Response(
                {"detail": "Invalid user ID"},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {"detail": "Đã xảy ra lỗi khi cập nhật số lượng"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @require_auth
    def delete(self, request, cartItemId):
        """Remove item from cart"""
        try:
            user_id = request.user_claims['sub']
            user = User.objects(id=ObjectId(user_id)).first()
            
            if not user:
                return Response(
                    {"detail": "User not found"},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Get cart
            cart = Cart.objects(user=user).first()
            if not cart:
                return Response(
                    {"detail": "Không tìm thấy sản phẩm trong giỏ hàng"},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Parse cartItemId as index
            try:
                item_index = int(cartItemId)
            except ValueError:
                return Response(
                    {"detail": "Invalid cart item ID"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Validate index
            if item_index < 0 or item_index >= len(cart.products):
                return Response(
                    {"detail": "Không tìm thấy sản phẩm trong giỏ hàng"},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Remove item
            cart.products.pop(item_index)
            cart.save()
            
            return Response(
                {"message": "Đã xóa sản phẩm khỏi giỏ hàng"},
                status=status.HTTP_200_OK
            )
            
        except InvalidId:
            return Response(
                {"detail": "Invalid user ID"},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {"detail": "Đã xảy ra lỗi khi xóa sản phẩm khỏi giỏ hàng"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CartCountView(APIView):
    """GET /api/cart/count - Get total quantity in cart"""
    
    @require_auth
    def get(self, request):
        try:
            user_id = request.user_claims['sub']
            user = User.objects(id=ObjectId(user_id)).first()
            
            if not user:
                return Response(
                    {"detail": "User not found"},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            cart = Cart.objects(user=user).first()
            total_count = sum(item.quantity for item in cart.products) if cart else 0
            
            return Response({"count": total_count}, status=status.HTTP_200_OK)
            
        except InvalidId:
            return Response(
                {"detail": "Invalid user ID"},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {"detail": "Đã xảy ra lỗi khi lấy số lượng giỏ hàng"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class VoucherValidateView(APIView):
    """POST /api/vouchers/validate - Validate voucher code"""
    
    @require_auth
    def post(self, request):
        """Validate voucher code - TODO: Implement voucher validation logic"""
        return Response(
            {"detail": "Voucher validation endpoint - Not yet implemented"},
            status=status.HTTP_501_NOT_IMPLEMENTED
        )


class OrderCreateView(APIView):
    """POST /api/orders - Create new order"""
    
    @require_auth
    def post(self, request):
        """Create new order from cart - TODO: Implement order creation logic"""
        return Response(
            {"detail": "Order creation endpoint - Not yet implemented"},
            status=status.HTTP_501_NOT_IMPLEMENTED
        )


# ==================== VOUCHER USER VIEWS ====================

def _serialize_user_voucher(user_voucher, include_voucher_details=True):
    """Serialize user voucher to dict"""
    data = {
        "_id": str(user_voucher.id),
        "addedAt": user_voucher.added_at.isoformat() if user_voucher.added_at else None,
        "status": user_voucher.status,
        "usedAt": user_voucher.used_at.isoformat() if user_voucher.used_at else None
    }
    
    if include_voucher_details and user_voucher.voucher:
        voucher = user_voucher.voucher
        voucher_data = {
            "_id": str(voucher.id),
            "name": voucher.name,
            "code": voucher.code,
            "description": voucher.description or "",
            "discount": voucher.discount,
            "min_value": voucher.min_value,
            "start_date": voucher.start_date.isoformat() if voucher.start_date else None,
            "expired_date": voucher.expired_date.isoformat() if voucher.expired_date else None,
            "categories": [str(cat_id) for cat_id in voucher.categories] if voucher.categories else []
        }
        data["voucher"] = voucher_data
    
    return data


def _get_voucher_status_for_user(voucher):
    """Get voucher status for user: active, expired"""
    now = datetime.utcnow()
    if voucher.expired_date and voucher.expired_date < now:
        return "expired"
    if voucher.start_date and voucher.start_date > now:
        return "upcoming"
    return "active"


class UserVoucherListView(APIView):
    """GET /api/vouchers - Get user's vouchers"""
    
    @require_auth
    def get(self, request):
        """Get list of vouchers user has added"""
        try:
            user_id = request.user_claims['sub']
            user = User.objects(id=ObjectId(user_id)).first()
            
            if not user:
                return Response(
                    {"detail": "User not found"},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Get status filter
            status_filter = (request.query_params.get("status") or "").strip().lower()
            
            # Get user vouchers
            user_vouchers = UserVoucher.objects(user=user)
            
            # Filter by status if provided
            # Note: We'll filter after loading since MongoEngine doesn't support nested field queries easily
            user_vouchers_list = list(user_vouchers)
            
            if status_filter:
                now = datetime.utcnow()
                filtered = []
                for uv in user_vouchers_list:
                    if uv.voucher:
                        uv.voucher.reload()
                        if status_filter == "active":
                            # Active = not expired, not used, and started
                            if (uv.status == "active" and 
                                (not uv.voucher.expired_date or uv.voucher.expired_date >= now) and
                                (not uv.voucher.start_date or uv.voucher.start_date <= now)):
                                filtered.append(uv)
                        elif status_filter == "expired":
                            # Expired = expired_date < now
                            if uv.voucher.expired_date and uv.voucher.expired_date < now:
                                filtered.append(uv)
                        elif status_filter == "used":
                            if uv.status == "used":
                                filtered.append(uv)
                user_vouchers_list = filtered
            
            # Sort by added_at descending
            user_vouchers_list.sort(key=lambda x: x.added_at or datetime.min, reverse=True)
            
            # Serialize
            result = []
            now = datetime.utcnow()
            for uv in user_vouchers_list:
                # Reload voucher reference
                if uv.voucher:
                    uv.voucher.reload()
                    
                    # Update status if expired
                    if uv.status == "active" and uv.voucher.expired_date and uv.voucher.expired_date < now:
                        uv.status = "expired"
                        uv.save()
                
                result.append(_serialize_user_voucher(uv, include_voucher_details=True))
            
            return Response({"data": result})
            
        except InvalidId:
            return Response(
                {"detail": "Invalid user ID"},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {"detail": f"Đã xảy ra lỗi: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class AddVoucherView(APIView):
    """POST /api/addVoucher - Add voucher to user's account"""
    
    @require_auth
    def post(self, request):
        """Add voucher by code"""
        try:
            user_id = request.user_claims['sub']
            user = User.objects(id=ObjectId(user_id)).first()
            
            if not user:
                return Response(
                    {"detail": "User not found"},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Get code from request
            code = request.data.get('code')
            if not code:
                return Response(
                    {"detail": "code là bắt buộc"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Normalize code
            code = code.upper().strip()
            
            # Find voucher by code
            voucher = Voucher.objects(code=code).first()
            if not voucher:
                return Response(
                    {"detail": "Mã voucher không hợp lệ"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Check if voucher is valid (not expired, started)
            now = datetime.utcnow()
            if voucher.expired_date and voucher.expired_date < now:
                return Response(
                    {"detail": "Voucher đã hết hạn"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if voucher.start_date and voucher.start_date > now:
                return Response(
                    {"detail": "Voucher chưa có hiệu lực"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Check if user already has this voucher
            existing = UserVoucher.objects(user=user, voucher=voucher).first()
            if existing:
                return Response(
                    {"detail": "Voucher đã được thêm vào tài khoản"},
                    status=status.HTTP_409_CONFLICT
                )
            
            # Create user voucher
            user_voucher = UserVoucher(
                user=user,
                voucher=voucher,
                status="active"
            )
            user_voucher.save()
            
            # Reload voucher reference for serialization
            user_voucher.voucher.reload()
            
            return Response(
                _serialize_user_voucher(user_voucher, include_voucher_details=True),
                status=status.HTTP_200_OK
            )
            
        except InvalidId:
            return Response(
                {"detail": "Invalid user ID"},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {"detail": f"Đã xảy ra lỗi: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class RemoveVoucherView(APIView):
    """DELETE /api/removeVoucher - Remove voucher from user's account"""
    
    @require_auth
    def delete(self, request):
        """Remove voucher from user account"""
        try:
            user_id = request.user_claims['sub']
            user = User.objects(id=ObjectId(user_id)).first()
            
            if not user:
                return Response(
                    {"detail": "User not found"},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Get voucherId from request body
            voucher_id = request.data.get('voucherId')
            if not voucher_id:
                return Response(
                    {"detail": "voucherId là bắt buộc"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Find user voucher
            try:
                voucher_obj_id = ObjectId(voucher_id)
            except InvalidId:
                return Response(
                    {"detail": "Invalid voucher ID"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Find voucher first
            voucher = Voucher.objects(id=voucher_obj_id).first()
            if not voucher:
                return Response(
                    {"detail": "Voucher không tồn tại"},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            user_voucher = UserVoucher.objects(user=user, voucher=voucher).first()
            if not user_voucher:
                return Response(
                    {"detail": "Voucher không tồn tại trong danh sách của bạn"},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Delete user voucher
            user_voucher.delete()
            
            return Response(
                {"message": "Xóa mã giảm giá thành công!"},
                status=status.HTTP_200_OK
            )
            
        except InvalidId:
            return Response(
                {"detail": "Invalid user ID"},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {"detail": f"Đã xảy ra lỗi: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


