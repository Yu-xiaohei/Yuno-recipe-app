# The API-33 implementation must not be inlined into the API-31 entry point.
# The boundary is retained even in the compressed compatibility candidate.
-keep class com.yunobase.recipe.compat.EnhancedMaterial** { *; }
-keep class com.yunobase.recipe.compat.LensKt { *; }
