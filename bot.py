async def scan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔎 Scanning BTC/USDT...")

    try:
        signal = await asyncio.to_thread(grid_engine.get_scalp_signal, config.PAIR)
    except Exception as e:
        await update.message.reply_text(f"❌ INTERNAL SCAN ERROR: {e}")
        return

    if not signal:
        await update.message.reply_text("😐 No good scalp setup right now (mid-range or dead volume).")
        return

    msg = (
        f"🎯 SCALP SIGNAL ({config.PAIR})\n"
        f"Side: {signal['side']}\n"
        f"Entry: {signal['entry']:.4f}\n"
        f"TP: {signal['tp']:.4f}\n"
        f"SL: {signal['sl']:.4f}\n\n"
        f"Range: {signal['low']:.4f} — {signal['high']:.4f}\n"
        f"ATR: {signal['atr']:.4f}\n\n"
        f"Reason: {signal['reason']}\n"
        f"⚠️ SIGNAL ONLY — no real trades yet"
    )

    await update.message.reply_text(msg)
