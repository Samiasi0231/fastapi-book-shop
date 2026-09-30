from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Float,
    Boolean
)
from sqlalchemy.orm import (
    declarative_base,
    sessionmaker,
    Session
)


app = FastAPI(title="Bookstore API")



DATABASE_URL = "sqlite:///./bookstore.db"


engine = create_engine(
    DATABASE_URL,
    connect_args={
        "check_same_thread": False
    }
)


Base = declarative_base()


SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)



def get_db():

    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()






class Book(Base):

    __tablename__ = "books"


    id = Column(
        Integer,
        primary_key=True,
        index=True
    )


    title = Column(
        String,
        nullable=False
    )


    author = Column(
        String,
        nullable=False
    )


    price = Column(
        Float,
        nullable=False
    )


    category = Column(
        String,
        nullable=False
    )


    in_stock = Column(
        Boolean,
        default=True
    )


    published_year = Column(
        Integer,
        nullable=True
    )

Base.metadata.create_all(bind=engine)
class BookBase(BaseModel):

    title: str

    author: str

    price: float

    category: str

    in_stock: bool = True

    published_year: int | None = None

class BookCreate(BookBase):

    pass

class BookUpdate(BaseModel):

    title: str | None = None

    author: str | None = None

    price: float | None = None

    category: str | None = None

    in_stock: bool | None = None

    published_year: int | None = None

class BookResponse(BookBase):

    id: int


    class Config:

        from_attributes = True

@app.post(
    "/books/",
    response_model=BookResponse
)
def create_book(
    book: BookCreate,
    db: Session = Depends(get_db)
):

    new_book = Book(
        title=book.title,
        author=book.author,
        price=book.price,
        category=book.category,
        in_stock=book.in_stock,
        published_year=book.published_year
    )


    db.add(new_book)

    db.commit()

    db.refresh(new_book)


    return new_book

@app.get(
    "/books/",
    response_model=list[BookResponse]
)
def get_books(
    category: str | None = None,

    published_after: int | None = None,

    max_price: float | None = None,

    sort_by: str | None = None,

    limit: int = 10,

    skip: int = 0,

    db: Session = Depends(get_db)
):


    query = db.query(Book)



    if category:

        query = query.filter(
            Book.category == category
        )

    if published_after:

        query = query.filter(
            Book.published_year > published_after
        )

    if max_price:

        query = query.filter(
            Book.price <= max_price
        )

    if sort_by == "price":

        query = query.order_by(
            Book.price
        )

    books = query.offset(
        skip
    ).limit(
        limit
    ).all()
    return books

@app.get(
    "/books/{book_id}",
    response_model=BookResponse
)
def get_book(
    book_id: int,
    db: Session = Depends(get_db)
):

    book = db.query(Book).filter(
        Book.id == book_id
    ).first()

    if not book:

        raise HTTPException(
            status_code=404,
            detail="Book not found"
        )


    return book

@app.get("/categories/")
def get_categories(
    db: Session = Depends(get_db)
):

    categories = db.query(
        Book.category
    ).distinct().all()


    return [
        category[0]
        for category in categories
    ]
@app.get(
    "/categories/{category}",
    response_model=list[BookResponse]
)
def get_books_by_category(
    category: str,
    db: Session = Depends(get_db)
):

    books = db.query(Book).filter(
        Book.category == category
    ).all()
    return books

@app.put(
    "/books/{book_id}",
    response_model=BookResponse
)
def update_book(
    book_id: int,
    book_data: BookCreate,
    db: Session = Depends(get_db)
):

    book = db.query(Book).filter(
        Book.id == book_id
    ).first()

    if not book:

        raise HTTPException(
            status_code=404,
            detail="Book not found"
        )

    book.title = book_data.title

    book.author = book_data.author

    book.price = book_data.price

    book.category = book_data.category

    book.in_stock = book_data.in_stock

    book.published_year = book_data.published_year

    db.commit()
    db.refresh(book)
    return book

@app.patch(
    "/books/{book_id}",
    response_model=BookResponse
)
def patch_book(
    book_id: int,
    book_data: BookUpdate,
    db: Session = Depends(get_db)
):
    book = db.query(Book).filter(
        Book.id == book_id
    ).first()
    if not book:
        raise HTTPException(
            status_code=404,
            detail="Book not found"
        )
    update_data = book_data.model_dump(
        exclude_unset=True
    )
    for key, value in update_data.items():

        setattr(
            book,
            key,
            value
        )
    db.commit()
    db.refresh(book)
    return book


@app.delete(
    "/books/{book_id}"
)
def delete_book(
    book_id: int,
    db: Session = Depends(get_db)
):

    book = db.query(Book).filter(
        Book.id == book_id
    ).first()

    if not book:
        raise HTTPException(
            status_code=404,
            detail="Book not found"
        )
    db.delete(book)
    db.commit()
    return {
        "message": "Book deleted successfully"
    }