from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    """
    Classe base per tutti i modelli SQLAlchemy.
    Implementa la modalità 'declarativa' di SQLAlchemy, che permette di definire 
    i modelli senza specificare esplicitamente le colonne e le relazioni.
    """
    pass
