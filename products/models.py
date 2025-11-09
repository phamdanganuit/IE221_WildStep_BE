"""
Products module models: Brand, Category, Product
"""
import mongoengine as me
from datetime import datetime
from django.utils.text import slugify


class Brand(me.Document):
    """Brand model - Thương hiệu sản phẩm"""
    # name, description hỗ trợ đa ngôn ngữ: string hoặc dict {vi,en,ja}
    name = me.DynamicField(required=True)
    slug = me.StringField(required=True, unique=True, max_length=250)
    description = me.DynamicField()
    logo = me.StringField()  # URL to logo image
    website = me.StringField()
    country = me.StringField(max_length=100)
    status = me.StringField(
        choices=["active", "inactive"],
        default="active"
    )
    created_at = me.DateTimeField(default=datetime.utcnow)
    updated_at = me.DateTimeField(default=datetime.utcnow)
    
    meta = {
        "collection": "brands",
        "indexes": [
            "slug",
            "name",
            "status"
        ]
    }
    
    def save(self, *args, **kwargs):
        """Auto-generate slug from name if not provided"""
        if not self.slug:
            # Generate slug from name (support dict or string)
            source_name = None
            if isinstance(self.name, dict):
                source_name = self.name.get('vi') or self.name.get('en') or self.name.get('ja')
                if not source_name:
                    # pick any first value
                    try:
                        source_name = next(iter(self.name.values()))
                    except Exception:
                        source_name = ''
            else:
                source_name = self.name or ''
            base_slug = slugify(source_name)
            # Ensure unique slug
            counter = 1
            unique_slug = base_slug
            while Brand.objects(slug=unique_slug, id__ne=self.id).first():
                unique_slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = unique_slug
        
        self.updated_at = datetime.utcnow()
        return super(Brand, self).save(*args, **kwargs)
    
    def __str__(self):
        return self.name


class ParentCategory(me.Document):
    """Parent Category - Danh mục cha"""
    name = me.DynamicField(required=True)
    slug = me.StringField(required=True, unique=True, max_length=250)
    description = me.DynamicField()
    image = me.StringField()  # URL to category image
    status = me.StringField(
        choices=["active", "inactive"],
        default="active"
    )
    created_at = me.DateTimeField(default=datetime.utcnow)
    updated_at = me.DateTimeField(default=datetime.utcnow)
    
    meta = {
        "collection": "parent_categories",
        "indexes": [
            "slug",
            "name",
            "status"
        ]
    }
    
    def save(self, *args, **kwargs):
        """Auto-generate slug from name if not provided"""
        if not self.slug:
            base_slug = slugify(self.name)
            counter = 1
            unique_slug = base_slug
            while ParentCategory.objects(slug=unique_slug, id__ne=self.id).first():
                unique_slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = unique_slug
        
        self.updated_at = datetime.utcnow()
        return super(ParentCategory, self).save(*args, **kwargs)
    
    def __str__(self):
        return self.name


class ChildCategory(me.Document):
    """Child Category - Danh mục con (subcategory)"""
    name = me.DynamicField(required=True)
    slug = me.StringField(required=True, unique=True, max_length=250)
    description = me.DynamicField()
    image = me.StringField()  # URL to category image
    parent = me.ReferenceField(ParentCategory, required=True)
    status = me.StringField(
        choices=["active", "inactive"],
        default="active"
    )
    created_at = me.DateTimeField(default=datetime.utcnow)
    updated_at = me.DateTimeField(default=datetime.utcnow)
    
    meta = {
        "collection": "child_categories",
        "indexes": [
            "slug",
            "name",
            "parent",
            "status"
        ]
    }
    
    def save(self, *args, **kwargs):
        """Auto-generate slug from name if not provided"""
        if not self.slug:
            base_slug = slugify(self.name)
            counter = 1
            unique_slug = base_slug
            while ChildCategory.objects(slug=unique_slug, id__ne=self.id).first():
                unique_slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = unique_slug
        
        self.updated_at = datetime.utcnow()
        return super(ChildCategory, self).save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.parent.name} > {self.name}"


class ColorVariant(me.EmbeddedDocument):
    """Color variant embedded in Product"""
    color_name = me.DynamicField(required=True)  # Support multilingual
    hex_color = me.StringField()  # Hex color code, e.g. #FF5733
    image = me.StringField()  # URL to color variant image
    tags = me.ListField(me.StringField())


class SizeVariant(me.EmbeddedDocument):
    """Size variant embedded in Product"""
    size_name = me.DynamicField(required=True)  # Support multilingual
    tags = me.ListField(me.StringField())


class Product(me.Document):
    """Product model - Sản phẩm"""
    # Basic info
    name = me.DynamicField(required=True)
    slug = me.StringField(required=True, unique=True, max_length=350)
    description = me.DynamicField()
    
    # Pricing
    original_price = me.FloatField(required=True, min_value=0)  # originalPrice trong DB
    discount = me.FloatField(default=0, min_value=0, max_value=100)  # % discount
    discount_price = me.FloatField(min_value=0)  # Calculated or manual price after discount
    
    # Inventory
    stock = me.IntField(default=0, min_value=0)
    sold = me.IntField(default=0, min_value=0)
    
    # Rating
    rate = me.FloatField(default=0, min_value=0, max_value=5)
    
    # Media
    images = me.ListField(me.StringField(), default=list)
    
    # Relationships
    brand = me.ReferenceField(Brand, required=True)
    category = me.ReferenceField(ChildCategory, required=True)
    
    # Variants (embedded)
    colors = me.EmbeddedDocumentListField(ColorVariant, default=list)
    sizes = me.EmbeddedDocumentListField(SizeVariant, default=list)
    size_table = me.DynamicField()  # Size chart/table info (can be localized)
    
    # Product attributes (all support multilingual)
    gender = me.DynamicField()  # Gender: male, female, unisex (can be localized)
    material = me.DynamicField()  # Material description (can be localized)
    weight = me.DynamicField()  # Weight info (can be localized or number)
    size = me.DynamicField()  # General size info (can be localized)
    
    # Additional info from API spec
    status = me.StringField(
        choices=["active", "inactive", "out_of_stock", "low_stock"],
        default="active"
    )
    tags = me.ListField(me.StringField(), default=list)
    
    # Legacy field - kept for backward compatibility with old data
    # This field is deprecated and should not be used in new code
    specifications = me.DictField()  # DEPRECATED: Use gender, material, weight, size instead
    
    # Timestamps
    created_at = me.DateTimeField(default=datetime.utcnow)
    updated_at = me.DateTimeField(default=datetime.utcnow)
    
    meta = {
        "collection": "products",
        "indexes": [
            "slug",
            "name",
            "brand",
            "category",
            "status",
            "created_at"
            # Note: Text index for full-text search can be created manually in MongoDB if needed
        ]
    }
    
    def save(self, *args, **kwargs):
        """Auto-generate slug and calculate discount_price"""
        # Generate slug from name if not provided (support multilingual)
        if not self.slug:
            source_name = None
            if isinstance(self.name, dict):
                source_name = self.name.get('vi') or self.name.get('en') or self.name.get('ja')
                if not source_name:
                    try:
                        source_name = next(iter(self.name.values()))
                    except Exception:
                        source_name = ''
            else:
                source_name = self.name or ''
            base_slug = slugify(source_name)
            counter = 1
            unique_slug = base_slug
            while Product.objects(slug=unique_slug, id__ne=self.id).first():
                unique_slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = unique_slug
        
        # Calculate discount_price if not manually set
        if self.discount and self.discount > 0:
            if not self.discount_price:
                self.discount_price = self.original_price * (1 - self.discount / 100)
        else:
            self.discount_price = None
        
        # Auto-update status based on stock
        if self.stock == 0:
            self.status = "out_of_stock"
        elif self.stock < 10:  # Low stock threshold
            if self.status != "inactive":
                self.status = "low_stock"
        
        self.updated_at = datetime.utcnow()
        return super(Product, self).save(*args, **kwargs)
    
    def __str__(self):
        return self.name


class Banner(me.Document):
    """Homepage banner"""
    image = me.StringField(required=True)
    link = me.StringField()
    title = me.DynamicField()
    order = me.IntField(default=0)
    status = me.StringField(choices=["active", "inactive"], default="active")
    created_at = me.DateTimeField(default=datetime.utcnow)
    updated_at = me.DateTimeField(default=datetime.utcnow)

    meta = {"collection": "banners", "indexes": ["status", "order"]}

    def save(self, *args, **kwargs):
        self.updated_at = datetime.utcnow()
        return super(Banner, self).save(*args, **kwargs)


class HeroContent(me.Document):
    """Hero section content (singleton-ish)"""
    headline = me.StringField(required=True)
    subtext = me.StringField()
    cta_text = me.StringField()
    cta_url = me.StringField()
    image = me.StringField()  # URL
    status = me.StringField(choices=["active", "inactive"], default="active")
    created_at = me.DateTimeField(default=datetime.utcnow)
    updated_at = me.DateTimeField(default=datetime.utcnow)

    meta = {"collection": "hero_content", "indexes": ["status", "-created_at"]}

    def save(self, *args, **kwargs):
        self.updated_at = datetime.utcnow()
        return super(HeroContent, self).save(*args, **kwargs)


class CustomerReview(me.Document):
    """Customer reviews for public display"""
    author_name = me.StringField(required=True)
    author_avatar = me.StringField()
    rating = me.IntField(min_value=1, max_value=5, default=5)
    content = me.StringField(required=True)
    placement = me.StringField(default="home")  # e.g., home
    status = me.StringField(choices=["active", "inactive"], default="active")
    created_at = me.DateTimeField(default=datetime.utcnow)

    meta = {"collection": "customer_reviews", "indexes": ["placement", "status", "-created_at"]}