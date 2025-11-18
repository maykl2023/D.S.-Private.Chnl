from aiogram import Bot, Dispatcher, types, Router, F
from aiogram.filters import Command
from aiogram.types import LabeledPrice, PreCheckoutQuery, InlineKeyboardMarkup, InlineKeyboardButton
import asyncio
import logging
import os
import aiohttp  # для крипто-чеков

BOT_TOKEN = os.getenv("BOT_TOKEN")
PROVIDER_TOKEN = os.getenv("PROVIDER_TOKEN", "")  # для карт, если подключишь
CRYPTO_API_KEY = os.getenv("CRYPTO_API_KEY", "")  # для крипты, если подключишь

CHANNEL_1 = int(os.getenv("CHANNEL_1", "-1001234567890"))  # ID первого канала
CHANNEL_2 = int(os.getenv("CHANNEL_2", "-1009876543210"))  # ID второго канала

PRICES = {
    "vip1": 4900,    # Stars для канала 1
    "vip2": 5900,    # для канала 2
    "both": 8000     # для обоих
}

bot = Bot(token=BOT_TOKEN, parse_mode="HTML")
dp = Dispatcher()
router = Router()

@router.message(Command("start"))
async def start(m: types.Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Доступ к VIP1 (4900 ⭐)", callback_data="select_vip1")],
        [InlineKeyboardButton(text="Доступ к VIP2 (5900 ⭐)", callback_data="select_vip2")],
        [InlineKeyboardButton(text="Оба канала (8000 ⭐)", callback_data="select_both")]
    ])
    await m.answer(
        "Привет! Выбери доступ к каналам:\n"
        "• VIP1: Эксклюзивный контент №1\n"
        "• VIP2: Эксклюзивный контент №2\n"
        "• Оба: Полный пакет",
        reply_markup=kb
    )

@router.callback_query(F.data.startswith("select_"))
async def select_channel(call: types.CallbackQuery):
    choice = call.data.split("_")[1]  # vip1, vip2, both
    choice_name = {"vip1": "VIP1", "vip2": "VIP2", "both": "Оба канала"}.get(choice, choice)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Оплатить Звёздами", callback_data=f"pay_stars_{choice}")],
        [InlineKeyboardButton(text="Оплатить картой", callback_data=f"pay_fiat_{choice}")],
        [InlineKeyboardButton(text="Оплатить криптой", callback_data=f"pay_crypto_{choice}")]
    ])
    await call.message.edit_text(
        f"Выбрано: {choice_name}\n"
        f"Цена: {PRICES[choice]} Stars (~{PRICES[choice]/100} ₽)\nВыбери способ оплаты:",
        reply_markup=kb
    )

@router.callback_query(F.data.startswith("pay_stars_"))
async def pay_stars(call: types.CallbackQuery):
    choice = call.data.split("_")[2]
    await bot.send_invoice(
        chat_id=call.from_user.id,
        title=f"Доступ к {choice}",
        description="Цифровой доступ к каналу(ам)",
        payload=f"stars_{choice}",
        provider_token="",  # Для Звёзд
        currency="XTR",
        prices=[LabeledPrice(label="Доступ", amount=PRICES[choice])],
        start_parameter="vip-access"
    )
    await call.answer()

@router.callback_query(F.data.startswith("pay_fiat_"))
async def pay_fiat(call: types.CallbackQuery):
    choice = call.data.split("_")[2]
    await bot.send_invoice(
        chat_id=call.from_user.id,
        title=f"Доступ к {choice}",
        description="Оплата картой или Apple/Google Pay",
        payload=f"fiat_{choice}",
        provider_token=PROVIDER_TOKEN,
        currency="RUB",  # Можно USD/EUR
        prices=[LabeledPrice(label="Доступ", amount=PRICES[choice] * 100)],  # В копейках
        start_parameter="fiat-access"
    )
    await call.answer()

@router.callback_query(F.data.startswith("pay_crypto_"))
async def pay_crypto(call: types.CallbackQuery):
    choice = call.data.split("_")[2]
    # Пример для CryptoCloud — замени на свой API, если подключишь
    pay_link = f"https://pay.cryptocloud.plus/pay?amount={PRICES[choice]/100}&order_id={call.from_user.id}_{choice}"  # Тестовая ссылка
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Оплатить криптой (BTC/ETH/TON/USDT)", url=pay_link)]
    ])
    await call.message.edit_text(
        f"Перейди по ссылке для оплаты криптой ({PRICES[choice]/100} USD):\n"
        f"Поддержка: BTC, ETH, TON, USDT и 2000+ монет.\n"
        f"После оплаты бот пришлёт доступ (5–10 мин).",
        reply_markup=kb
    )
    await call.answer()

@router.pre_checkout_query()
async def pre_checkout(p: PreCheckoutQuery):
    await bot.answer_pre_checkout_query(p.id, ok=True)

@router.message(F.successful_payment)
async def success(m: types.Message):
    choice = m.successful_payment.invoice_payload.split("_")[1]  # vip1, vip2, both
    channels = []
    if choice in ["vip1", "both"]:
        link1 = await bot.create_chat_invite_link(CHANNEL_1, member_limit=1, name=f"Доступ {m.from_user.id}")
        channels.append(f"• VIP1: {link1.invite_link}")
    if choice in ["vip2", "both"]:
        link2 = await bot.create_chat_invite_link(CHANNEL_2, member_limit=1, name=f"Доступ {m.from_user.id}")
        channels.append(f"• VIP2: {link2.invite_link}")

    await m.answer(
        f"Оплата прошла! ✅ Твои личные доступы (одноразовые ссылки):\n" + "\n".join(channels) +
        "\n\nЕсли крипта — подтверждение придёт скоро. Наслаждайся контентом!"
    )

dp.include_router(router)

async def main():
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
