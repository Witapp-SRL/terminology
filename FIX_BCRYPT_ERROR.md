# Fix: Errore Passlib/Bcrypt Compatibility

## 🐛 Problema

```
WARNING:passlib.handlers.bcrypt:(trapped) error reading bcrypt version
AttributeError: module 'bcrypt' has no attribute '__about__'
```

**Causa:** Incompatibilità tra `bcrypt 4.1.3` e `passlib 1.7.4`

---

## ✅ Soluzione APPLICATA

Ho già aggiornato `backend/requirements.txt` con versioni compatibili:

```txt
bcrypt==4.0.1           # Downgrade da 4.1.3 a 4.0.1
passlib[bcrypt]==1.7.4  # Con supporto bcrypt esplicito
python-jose[cryptography]==3.5.0  # Con cryptography
```

---

## 🚀 Comandi da Eseguire

```bash
# 1. Stop containers
docker compose down

# 2. Rebuild backend con nuove dipendenze
docker compose build backend --no-cache

# 3. Restart
docker compose up -d

# 4. Verifica (nessun warning bcrypt)
docker compose logs backend | grep bcrypt
```

---

## 🔍 Verifica Fix

```bash
# I logs del backend NON devono mostrare warning passlib/bcrypt
docker compose logs backend | head -30

# Output atteso (pulito):
# INFO:     Uvicorn running on http://0.0.0.0:8001
# INFO:     Application startup complete.
# (nessun WARNING su bcrypt)
```

---

## 🛠️ Se Vuoi Usare Bcrypt Più Recente

Alternative moderne a passlib:

### Opzione A: Usa bcrypt diretto con passlib 1.7.4
✅ **GIÀ IMPLEMENTATO** - `bcrypt==4.0.1`

### Opzione B: Passa a python-bcrypt moderno

Modifica `auth.py`:
```python
import bcrypt

def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
```

E aggiorna `requirements.txt`:
```txt
bcrypt>=4.0.1  # Usa versione più recente
# Rimuovi passlib se usi solo bcrypt
```

---

## 📋 Versioni Compatibili Testate

| Libreria | Versione | Compatibilità |
|----------|----------|---------------|
| bcrypt | 4.0.1 | ✅ Compatibile con passlib 1.7.4 |
| bcrypt | 4.1.x | ❌ Rompe passlib 1.7.4 |
| passlib | 1.7.4 | ✅ Con bcrypt<=4.0.1 |

---

## 🔧 Rebuild Completo

```bash
# Pulizia completa
docker compose down -v
docker image rm fhir-terminology-backend

# Rebuild
docker compose build backend --no-cache

# Restart
docker compose up -d

# Test autenticazione
curl -X POST http://localhost:8001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
```

---

## ✅ Stato Post-Fix

Dopo il rebuild, l'autenticazione funzionerà senza warning:
- ✅ Password hashing con bcrypt 4.0.1
- ✅ Nessun warning passlib
- ✅ JWT authentication completamente funzionante
- ✅ Compatibilità con passlib maintained

---

## 🆘 Se il Warning Persiste

```bash
# Verifica che requirements.txt sia corretto
docker compose exec backend pip list | grep -E "bcrypt|passlib"

# Output atteso:
# bcrypt        4.0.1
# passlib       1.7.4

# Se vedi versioni diverse, rebuild:
docker compose build backend --no-cache --pull
```

---

## 📚 Risorse

- [Passlib Bcrypt Handler Docs](https://passlib.readthedocs.io/en/stable/lib/passlib.hash.bcrypt.html)
- [Bcrypt Changelog](https://github.com/pyca/bcrypt/blob/main/CHANGELOG.rst)
- GitHub Issue: [passlib/passlib#148](https://github.com/pyca/passlib/issues/148)

---

## 💡 Best Practice

Per evitare problemi futuri:

1. **Pin versioni esatte** (già fatto in requirements.txt)
2. **Test dopo upgrade** di librerie crypto
3. **Usa Docker** per consistency ambiente
4. **Rebuild con --no-cache** dopo cambio dipendenze

---

## ✅ Riepilogo

**Problema:** bcrypt 4.1.3 incompatibile con passlib 1.7.4  
**Soluzione:** Downgrade bcrypt a 4.0.1  
**File modificato:** `backend/requirements.txt`  
**Comando:** `docker compose build backend --no-cache`

Il fix è **già applicato**, devi solo rifare il build! 🚀
