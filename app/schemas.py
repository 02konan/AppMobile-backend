from marshmallow import (
    Schema,
    fields,
    validate,
    validates_schema,
    ValidationError,
)


# ============================================================
# VALIDATEURS COMMUNS
# ============================================================

USERNAME_REGEX = r"^[a-z0-9_]{3,30}$"

PHONE_REGEX = r"^\+?[0-9]{8,15}$"

EMAIL_REGEX = (
    r"^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@"
    r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?"
    r"(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?)+$"
)


# ============================================================
# INSCRIPTION
# ============================================================

class RegisterSchema(Schema):

    class Meta:
        unknown = "raise"

    name = fields.Str(
        required=True,
        allow_none=False,
        validate=validate.Length(
            min=2,
            max=100,
        ),
    )

    phone = fields.Str(
        required=True,
        allow_none=False,
        validate=[
            validate.Length(
                min=8,
                max=16,
            ),
            validate.Regexp(
                PHONE_REGEX,
                error="Numéro de téléphone invalide",
            ),
        ],
    )

    password = fields.Str(
        required=True,
        allow_none=False,
        validate=validate.Length(
            min=8,
            max=128,
        ),
    )

    role = fields.Str(
        load_default="buyer",
        validate=validate.OneOf(
            [
                "buyer",
                "merchant",
                "driver",
            ],
            error="Type de compte invalide",
        ),
    )

    email = fields.Email(
        allow_none=True,
        load_default=None,
    )

    firebaseIdToken = fields.Str(
        required=True,
        allow_none=False,
        validate=validate.Length(
            min=1,
            max=5000,
        ),
    )

    username = fields.Str(
        allow_none=True,
        load_default=None,
        validate=[
            validate.Length(
                min=3,
                max=30,
            ),
            validate.Regexp(
                USERNAME_REGEX,
                error="Nom d'utilisateur invalide",
            ),
        ],
    )

    country = fields.Str(
        allow_none=True,
        load_default=None,
        validate=validate.Length(
            max=100,
        ),
    )

    city = fields.Str(
        allow_none=True,
        load_default=None,
        validate=validate.Length(
            max=100,
        ),
    )

    otpCode = fields.Str(
        allow_none=True,
        load_default="",
        validate=validate.Length(
            max=20,
        ),
    )

    shopName = fields.Str(
        allow_none=True,
        load_default=None,
        validate=validate.Length(
            min=2,
            max=150,
        ),
    )


# ============================================================
# CONNEXION
# ============================================================

class LoginSchema(Schema):

    class Meta:
        unknown = "raise"

    phone = fields.Str(
        allow_none=True,
        load_default="",
        validate=validate.Length(
            max=16,
        ),
    )

    email = fields.Email(
        allow_none=True,
        load_default="",
    )

    password = fields.Str(
        required=True,
        allow_none=False,
        validate=validate.Length(
            min=1,
            max=128,
        ),
    )

    @validates_schema
    def validate_login_method(
        self,
        data,
        **kwargs,
    ):
        phone = data.get("phone")
        email = data.get("email")

        if not phone and not email:
            raise ValidationError(
                "Téléphone ou e-mail requis"
            )


# ============================================================
# MODIFICATION DU PROFIL
# ============================================================

class UpdateProfileSchema(Schema):

    class Meta:
        unknown = "raise"

    name = fields.Str(
        allow_none=False,
        validate=validate.Length(
            min=2,
            max=100,
        ),
    )

    address = fields.Str(
        allow_none=True,
        validate=validate.Length(
            max=500,
        ),
    )

    city = fields.Str(
        allow_none=True,
        validate=validate.Length(
            max=100,
        ),
    )

    country = fields.Str(
        allow_none=True,
        validate=validate.Length(
            max=100,
        ),
    )


# ============================================================
# AJOUT AU PANIER
# ============================================================

class AddToCartSchema(Schema):

    class Meta:
        unknown = "raise"

    productId = fields.Integer(
        required=True,
        strict=True,
        validate=validate.Range(
            min=1,
        ),
    )

    quantity = fields.Integer(
        load_default=1,
        strict=True,
        validate=validate.Range(
            min=1,
            max=100,
        ),
    )

    selectedColor = fields.Str(
        allow_none=True,
        load_default=None,
        validate=validate.Length(
            max=100,
        ),
    )

    selectedSize = fields.Str(
        allow_none=True,
        load_default=None,
        validate=validate.Length(
            max=100,
        ),
    )


# ============================================================
# MODIFICATION D'UN ARTICLE DU PANIER
# ============================================================

class UpdateCartItemSchema(Schema):

    class Meta:
        unknown = "raise"

    quantity = fields.Integer(
        required=True,
        strict=True,
        validate=validate.Range(
            min=1,
            max=100,
        ),
    )


# ============================================================
# CHECK USERNAME
# ============================================================

class UsernameQuerySchema(Schema):

    class Meta:
        unknown = "raise"

    username = fields.Str(
        required=True,
        validate=[
            validate.Length(
                min=3,
                max=30,
            ),
            validate.Regexp(
                USERNAME_REGEX,
                error="Nom d'utilisateur invalide",
            ),
        ],
    )