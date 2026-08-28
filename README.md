# ☁️ CloudNote - End-to-End Encrypted Cloud Notes Client

A privacy-focused desktop cloud note application using **AES-256-GCM + X25519 elliptic curve encryption** for true end-to-end encryption. The server only stores encrypted data and cannot decrypt user note content.

---

## ✨ Core Features

| Feature | Description |
|---------|-------------|
| ✓ End-to-End Encryption | Notes are encrypted locally before upload; the server never sees plaintext |
| ✓ Hybrid Encryption | X25519 key exchange + AES-256-GCM symmetric encryption |
| ✓ Flexible Key Management | Global key / per-file key / password protection modes |
| ✓ Two-Factor Protection | Combine password + separate key file to protect sensitive notes |
| ✓ Zero-Knowledge Architecture | The server stores no decryption keys |
| ✓ Cross-Platform | Windows / Linux / macOS |

---

## 🔐 Encryption Algorithms

- **Key Exchange**: X25519 (Elliptic Curve Diffie-Hellman)
- **Symmetric Encryption**: AES-256-GCM (Authenticated Encryption)
- **Asymmetric Encryption**: RSA-2048 (optional)
- **Key Derivation**: PBKDF2 (100,000 iterations)

---

## 🛠️ Tech Stack

- **Language**: Python 3.8+
- **GUI Framework**: PyQt5
- **Encryption Library**: cryptography
- **HTTP Client**: requests

---

## 🛡️ Security Principles

1. **Trust Not Needed** — The server is untrusted by default
2. **Keys Belong to User** — All keys exist only on the client
3. **Encrypt Locally** — Plaintext never leaves the user's device
4. **Open Source Verifiable** — Fully open source, open to security audit

---

## 📄 License

This project is licensed under the **Apache License 2.0**.

---

## 👤 Author

dvsxt

## 🔗 Repository

https://gitcode.com/dvsxt/cloudnote

---

## 🎵 For Music Lovers

> *Want to listen to some music while taking notes? Try my other project —*

### 🔊 ap_ds · The Lightweight Python Audio Revolution

**2.5MB** ends the era of FFmpeg's **160MB** bloat

- 🎵 Supports MP3 / FLAC / OGG / WAV
- ⚡ Non-blocking playback, perfect for GUI apps
- 📦 Zero dependencies, pure Python
- 🔒 v3.0 LTS long-term support, free forever

```bash
pip install ap_ds
```

```python
from ap_ds import AudioLibrary
lib = AudioLibrary()
lib.play_from_file("inspiration.mp3")  # listen while taking notes
```

👉 [Learn more about ap_ds](https://gitcode.com/dvsxt/ap_ds)

*From the same author, with the same values: lightweight, secure, pure.*
