from datetime import datetime
from extensions import db

class Recipe(db.Model):
    """레시피 모델"""
    __tablename__ = 'recipes'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(50))
    preparation_time = db.Column(db.Integer)  # 분 단위
    cooking_time = db.Column(db.Integer)      # 분 단위
    servings = db.Column(db.Integer)
    instructions = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 관계 설정
    ingredients = db.relationship('RecipeIngredient', back_populates='recipe', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Recipe {self.name}>'

class RecipeIngredient(db.Model):
    """레시피 재료 모델"""
    __tablename__ = 'recipe_ingredients'
    
    id = db.Column(db.Integer, primary_key=True)
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipes.id'), nullable=False)
    ingredient_id = db.Column(db.Integer, db.ForeignKey('ingredients.id'), nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    unit = db.Column(db.String(20), nullable=False)
    notes = db.Column(db.Text)
    
    # 관계 설정
    recipe = db.relationship('Recipe', back_populates='ingredients')
    ingredient = db.relationship('Ingredient')
    
    def __repr__(self):
        return f'<RecipeIngredient {self.ingredient_id} for Recipe {self.recipe_id}>' 