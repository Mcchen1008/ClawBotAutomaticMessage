from fastapi import FastAPI, Request, Depends, HTTPException, status, Form, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from ..config import ADMIN_USERNAME, ADMIN_PASSWORD, BASE_DIR
from ..database import get_db, init_db
from ..db.user_db import UserDB
from ..db.product_db import ProductDB
from ..db.card_db import CardDB
from ..db.order_db import OrderDB
from ..db.transaction_db import TransactionDB

templates_path = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(templates_path))


def check_admin_auth(request: Request):
    session = request.cookies.get("admin_session")
    if session != "authenticated":
        raise HTTPException(status_code=status.HTTP_302_FOUND, headers={"Location": "/admin/login"})
    return True


def create_app(bot_client=None) -> FastAPI:
    app = FastAPI(title="ClawBot微信虚拟商品售卖系统")

    init_db()

    @app.get("/", response_class=HTMLResponse)
    async def index():
        return RedirectResponse(url="/admin")

    @app.get("/admin/login", response_class=HTMLResponse)
    async def admin_login(request: Request):
        return templates.TemplateResponse(request, "login.html")

    @app.post("/admin/login")
    async def admin_login_post(username: str = Form(...), password: str = Form(...)):
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            response = RedirectResponse(url="/admin", status_code=302)
            response.set_cookie("admin_session", "authenticated", max_age=86400)
            return response
        return RedirectResponse(url="/admin/login?error=1", status_code=302)

    @app.get("/admin/logout")
    async def admin_logout():
        response = RedirectResponse(url="/admin/login", status_code=302)
        response.delete_cookie("admin_session")
        return response

    @app.get("/admin", response_class=HTMLResponse)
    async def admin_dashboard(request: Request, auth: bool = Depends(check_admin_auth)):
        with get_db() as conn:
            trans_db = TransactionDB(conn)
            stats = trans_db.get_statistics()
        return templates.TemplateResponse(request, "dashboard.html", {"stats": stats})

    @app.get("/admin/products", response_class=HTMLResponse)
    async def admin_products(request: Request, page: int = 1, auth: bool = Depends(check_admin_auth)):
        page_size = 20
        with get_db() as conn:
            product_db = ProductDB(conn)
            total = product_db.count_all()
            total_pages = max(1, (total + page_size - 1) // page_size)
            products = product_db.list_all(offset=(page - 1) * page_size, limit=page_size)
        return templates.TemplateResponse(request, "products.html", {
            "products": products,
            "page": page,
            "total_pages": total_pages,
        })

    @app.post("/admin/products/add")
    async def admin_product_add(
        name: str = Form(...),
        description: str = Form(""),
        price: float = Form(...),
        sort_order: int = Form(0),
        auth: bool = Depends(check_admin_auth),
    ):
        with get_db() as conn:
            product_db = ProductDB(conn)
            product_db.create(name=name, description=description, price=price, stock=0, sort_order=sort_order)
        return RedirectResponse(url="/admin/products", status_code=302)

    @app.post("/admin/products/{product_id}/edit")
    async def admin_product_edit(
        product_id: int,
        name: str = Form(...),
        description: str = Form(""),
        price: float = Form(...),
        is_active: int = Form(1),
        sort_order: int = Form(0),
        auth: bool = Depends(check_admin_auth),
    ):
        with get_db() as conn:
            product_db = ProductDB(conn)
            product_db.update(
                product_id,
                name=name,
                description=description,
                price=price,
                is_active=bool(is_active),
                sort_order=sort_order,
            )
        return RedirectResponse(url="/admin/products", status_code=302)

    @app.post("/admin/products/{product_id}/delete")
    async def admin_product_delete(product_id: int, auth: bool = Depends(check_admin_auth)):
        with get_db() as conn:
            product_db = ProductDB(conn)
            product_db.delete(product_id)
        return RedirectResponse(url="/admin/products", status_code=302)

    @app.get("/admin/products/{product_id}/cards", response_class=HTMLResponse)
    async def admin_product_cards(product_id: int, page: int = 1, used: str = "all",
                                  request: Request = None, auth: bool = Depends(check_admin_auth)):
        page_size = 50
        is_used = None
        if used == "used":
            is_used = True
        elif used == "unused":
            is_used = False

        with get_db() as conn:
            product_db = ProductDB(conn)
            card_db = CardDB(conn)
            product = product_db.get_by_id(product_id)
            total = card_db.count_product_cards(product_id=product_id, is_used=is_used)
            total_pages = max(1, (total + page_size - 1) // page_size)
            cards = card_db.list_product_cards(
                product_id=product_id,
                is_used=is_used,
                offset=(page - 1) * page_size,
                limit=page_size,
            )
        return templates.TemplateResponse(request, "product_cards.html", {
            "product": product,
            "cards": cards,
            "page": page,
            "total_pages": total_pages,
            "used": used,
        })

    @app.post("/admin/products/{product_id}/cards/add")
    async def admin_product_cards_add(
        product_id: int,
        card_data: str = Form(""),
        auth: bool = Depends(check_admin_auth),
    ):
        cards = []
        for line in card_data.strip().split("\n"):
            line = line.strip()
            if not line:
                continue
            parts = line.split("----")
            if len(parts) == 1:
                cards.append((parts[0], ""))
            elif len(parts) >= 2:
                cards.append((parts[0], parts[1]))

        with get_db() as conn:
            card_db = CardDB(conn)
            card_db.batch_add_product_cards(product_id, cards)
        return RedirectResponse(url=f"/admin/products/{product_id}/cards", status_code=302)

    @app.get("/admin/recharge-cards", response_class=HTMLResponse)
    async def admin_recharge_cards(page: int = 1, used: str = "all",
                                   request: Request = None, auth: bool = Depends(check_admin_auth)):
        page_size = 50
        is_used = None
        if used == "used":
            is_used = True
        elif used == "unused":
            is_used = False

        with get_db() as conn:
            card_db = CardDB(conn)
            total = card_db.count_recharge_cards(is_used=is_used)
            total_pages = max(1, (total + page_size - 1) // page_size)
            cards = card_db.list_recharge_cards(
                is_used=is_used,
                offset=(page - 1) * page_size,
                limit=page_size,
            )
        return templates.TemplateResponse(request, "recharge_cards.html", {
            "cards": cards,
            "page": page,
            "total_pages": total_pages,
            "used": used,
        })

    @app.post("/admin/recharge-cards/add")
    async def admin_recharge_cards_add(
        card_data: str = Form(""),
        amount: float = Form(0),
        auth: bool = Depends(check_admin_auth),
    ):
        cards = []
        for line in card_data.strip().split("\n"):
            line = line.strip()
            if not line:
                continue
            parts = line.split(",")
            if len(parts) == 1:
                cards.append((parts[0], amount))
            elif len(parts) >= 2:
                try:
                    amt = float(parts[1])
                except ValueError:
                    amt = amount
                cards.append((parts[0], amt))

        with get_db() as conn:
            card_db = CardDB(conn)
            card_db.batch_add_recharge_cards(cards)
        return RedirectResponse(url="/admin/recharge-cards", status_code=302)

    @app.get("/admin/users", response_class=HTMLResponse)
    async def admin_users(page: int = 1, keyword: str = "",
                          request: Request = None, auth: bool = Depends(check_admin_auth)):
        page_size = 20
        with get_db() as conn:
            user_db = UserDB(conn)
            if keyword:
                total = user_db.count_search(keyword)
                users = user_db.search(keyword, offset=(page - 1) * page_size, limit=page_size)
            else:
                total = user_db.count_all()
                users = user_db.list_all(offset=(page - 1) * page_size, limit=page_size)
            total_pages = max(1, (total + page_size - 1) // page_size)
        return templates.TemplateResponse(request, "users.html", {
            "users": users,
            "page": page,
            "total_pages": total_pages,
            "keyword": keyword,
        })

    @app.post("/admin/users/{user_db_id}/balance")
    async def admin_user_adjust_balance(
        user_db_id: int,
        amount: float = Form(...),
        action: str = Form(...),
        auth: bool = Depends(check_admin_auth),
    ):
        if action not in ("add", "sub"):
            return RedirectResponse(url="/admin/users", status_code=302)
        delta = abs(amount) if action == "add" else -abs(amount)
        with get_db() as conn:
            user_db = UserDB(conn)
            trans_db = TransactionDB(conn)
            user = user_db.get_by_id(user_db_id)
            if user:
                balance_before = user.balance
                updated = user_db.adjust_balance(user_db_id, delta)
                if updated:
                    trans_db.create(
                        user_id=user.id,
                        trans_type="recharge" if delta > 0 else "purchase",
                        amount=abs(delta),
                        balance_before=balance_before,
                        balance_after=updated.balance,
                        description=f"管理员调整余额({'+' if delta > 0 else '-'})",
                    )
        return RedirectResponse(url="/admin/users", status_code=302)

    @app.get("/admin/orders", response_class=HTMLResponse)
    async def admin_orders(page: int = 1, request: Request = None, auth: bool = Depends(check_admin_auth)):
        page_size = 20
        with get_db() as conn:
            order_db = OrderDB(conn)
            total = order_db.count_all()
            total_pages = max(1, (total + page_size - 1) // page_size)
            orders = order_db.list_all(offset=(page - 1) * page_size, limit=page_size)
        return templates.TemplateResponse(request, "orders.html", {
            "orders": orders,
            "page": page,
            "total_pages": total_pages,
        })

    @app.get("/admin/transactions", response_class=HTMLResponse)
    async def admin_transactions(page: int = 1, request: Request = None, auth: bool = Depends(check_admin_auth)):
        page_size = 50
        with get_db() as conn:
            trans_db = TransactionDB(conn)
            total = trans_db.count_all()
            total_pages = max(1, (total + page_size - 1) // page_size)
            transactions = trans_db.list_all(offset=(page - 1) * page_size, limit=page_size)
        return templates.TemplateResponse(request, "transactions.html", {
            "transactions": transactions,
            "page": page,
            "total_pages": total_pages,
        })

    @app.get("/api/v1/qrcode")
    async def api_qrcode():
        if not bot_client:
            return JSONResponse({"success": False, "message": "Bot未启动"})
        try:
            qrcode, qrcode_img = await bot_client.get_qrcode()
            return JSONResponse({
                "success": True,
                "data": {
                    "qrcode": qrcode,
                    "qrcode_url": qrcode_img,
                },
            })
        except Exception as e:
            return JSONResponse({"success": False, "message": str(e)})

    @app.get("/api/v1/qrcode/status")
    async def api_qrcode_status(qrcode: str):
        if not bot_client:
            return JSONResponse({"success": False, "message": "Bot未启动"})
        try:
            data = await bot_client.check_qrcode_status(qrcode)
            return JSONResponse({"success": True, "data": data})
        except Exception as e:
            return JSONResponse({"success": False, "message": str(e)})

    @app.get("/api/v1/users")
    async def api_users(page: int = 1, page_size: int = 20):
        with get_db() as conn:
            user_db = UserDB(conn)
            total = user_db.count_all()
            users = user_db.list_all(offset=(page - 1) * page_size, limit=page_size)
            return JSONResponse({
                "success": True,
                "data": {
                    "total": total,
                    "page": page,
                    "page_size": page_size,
                    "list": [{"id": u.id, "user_id": u.user_id, "balance": u.balance,
                              "wechat_id": u.wechat_id, "created_at": u.created_at}
                             for u in users],
                },
            })

    @app.get("/api/v1/products")
    async def api_products():
        with get_db() as conn:
            product_db = ProductDB(conn)
            products = product_db.list_all()
            return JSONResponse({
                "success": True,
                "data": [{"id": p.id, "name": p.name, "description": p.description,
                          "price": p.price, "stock": p.stock, "is_active": p.is_active}
                         for p in products],
            })

    @app.post("/api/v1/products")
    async def api_product_add(name: str, description: str = "", price: float = 0, sort_order: int = 0):
        with get_db() as conn:
            product_db = ProductDB(conn)
            p = product_db.create(name=name, description=description, price=price, stock=0, sort_order=sort_order)
            return JSONResponse({
                "success": True,
                "data": {"id": p.id, "name": p.name, "price": p.price},
            })

    @app.post("/api/v1/products/{product_id}/cards/batch")
    async def api_product_cards_batch(product_id: int, cards: list[dict]):
        card_list = [(c.get("code", ""), c.get("secret", "")) for c in cards]
        with get_db() as conn:
            card_db = CardDB(conn)
            count = card_db.batch_add_product_cards(product_id, card_list)
            return JSONResponse({"success": True, "data": {"added": count}})

    @app.post("/api/v1/recharge-cards/batch")
    async def api_recharge_cards_batch(cards: list[dict]):
        card_list = [(c.get("code", ""), c.get("amount", 0)) for c in cards]
        with get_db() as conn:
            card_db = CardDB(conn)
            count = card_db.batch_add_recharge_cards(card_list)
            return JSONResponse({"success": True, "data": {"added": count}})

    @app.get("/api/v1/orders")
    async def api_orders(page: int = 1, page_size: int = 20):
        with get_db() as conn:
            order_db = OrderDB(conn)
            total = order_db.count_all()
            orders = order_db.list_all(offset=(page - 1) * page_size, limit=page_size)
            return JSONResponse({
                "success": True,
                "data": {
                    "total": total,
                    "page": page,
                    "page_size": page_size,
                    "list": [{"id": o.id, "order_no": o.order_no, "user_id": o.user_id,
                              "product_name": o.product_name, "price": o.price,
                              "status": o.status, "created_at": o.created_at}
                             for o in orders],
                },
            })

    @app.get("/api/v1/stats")
    async def api_stats():
        with get_db() as conn:
            trans_db = TransactionDB(conn)
            stats = trans_db.get_statistics()
            return JSONResponse({"success": True, "data": stats})

    return app
