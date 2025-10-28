# PostgreSQL Setup Guide for FHIR Terminology Service

## Quick Start (Ubuntu/Debian)

### 1. Automated Setup

Run the automated setup script:

```bash
sudo chmod +x /app/backend/database/setup_ubuntu.sh
sudo /app/backend/database/setup_ubuntu.sh
```

The script will:
- Install PostgreSQL
- Create database and user
- Initialize schema
- Configure .env file

### 2. Manual Setup

If you prefer manual setup:

#### Install PostgreSQL

```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
```

#### Create Database and User

```bash
sudo -u postgres psql
```

```sql
-- Create user
CREATE USER fhir_user WITH PASSWORD 'your_secure_password';

-- Create database
CREATE DATABASE fhir_terminology OWNER fhir_user;

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE fhir_terminology TO fhir_user;

-- Exit
\q
```

#### Initialize Schema

```bash
sudo -u postgres psql -d fhir_terminology -f /app/backend/database/init_postgres.sql
```

#### Update .env Configuration

```bash
cp /app/backend/.env /app/backend/.env.sqlite.backup
```

Edit `/app/backend/.env`:

```env
DATABASE_URL=postgresql://fhir_user:your_password@localhost:5432/fhir_terminology
DB_NAME=fhir_terminology
CORS_ORIGINS=*
```

### 3. Install Python Dependencies

```bash
cd /app/backend
pip install psycopg2-binary
```

### 4. Seed Data

```bash
python /app/backend/seed_data_medical.py
```

### 5. Restart Backend

```bash
sudo supervisorctl restart backend
```

## Migration from SQLite

If you have existing data in SQLite:

```bash
python /app/backend/database/migrate_to_postgres.py
```

## Configuration Files

### PostgreSQL Main Config

`/etc/postgresql/{version}/main/postgresql.conf`

See `/app/backend/database/postgresql.conf.sample` for recommended settings.

### Client Authentication

`/etc/postgresql/{version}/main/pg_hba.conf`

See `/app/backend/database/pg_hba.conf.sample` for examples.

## Common PostgreSQL Commands

### Service Management

```bash
# Start PostgreSQL
sudo systemctl start postgresql

# Stop PostgreSQL
sudo systemctl stop postgresql

# Restart PostgreSQL
sudo systemctl restart postgresql

# Check status
sudo systemctl status postgresql
```

### Database Operations

```bash
# Connect to database
psql -U fhir_user -d fhir_terminology

# List databases
\l

# List tables
\dt

# Describe table
\d code_systems

# Check table sizes
\dt+

# Exit
\q
```

### Backup and Restore

```bash
# Backup database
pg_dump -U fhir_user fhir_terminology > backup.sql

# Restore database
psql -U fhir_user fhir_terminology < backup.sql

# Backup to compressed file
pg_dump -U fhir_user -F c fhir_terminology > backup.dump

# Restore from compressed file
pg_restore -U fhir_user -d fhir_terminology backup.dump
```

## Performance Tuning

### Analyze Tables

```sql
ANALYZE code_systems;
ANALYZE value_sets;
ANALYZE concept_maps;
```

### Vacuum

```sql
VACUUM ANALYZE;
```

### Check Index Usage

```sql
SELECT schemaname, tablename, indexname, idx_scan
FROM pg_stat_user_indexes
ORDER BY idx_scan;
```

## Monitoring

### Active Connections

```sql
SELECT * FROM pg_stat_activity 
WHERE datname = 'fhir_terminology';
```

### Database Size

```sql
SELECT pg_size_pretty(pg_database_size('fhir_terminology'));
```

### Table Sizes

```sql
SELECT 
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

## Troubleshooting

### Connection Issues

1. Check PostgreSQL is running:
   ```bash
   sudo systemctl status postgresql
   ```

2. Check connection settings in `postgresql.conf`:
   ```
   listen_addresses = 'localhost'
   ```

3. Check authentication in `pg_hba.conf`:
   ```
   host    fhir_terminology    fhir_user    127.0.0.1/32    md5
   ```

### Permission Issues

```sql
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO fhir_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO fhir_user;
```

### Performance Issues

1. Check slow queries in logs
2. Run ANALYZE on tables
3. Check index usage
4. Adjust memory settings in postgresql.conf

## Security Best Practices

1. **Use strong passwords**
2. **Limit network access** in pg_hba.conf
3. **Enable SSL** for remote connections
4. **Regular backups**
5. **Keep PostgreSQL updated**
6. **Monitor logs** for suspicious activity

## Remote Access (Optional)

To allow remote connections:

1. Edit `postgresql.conf`:
   ```
   listen_addresses = '*'
   ```

2. Edit `pg_hba.conf`:
   ```
   host    fhir_terminology    fhir_user    0.0.0.0/0    md5
   ```

3. Configure firewall:
   ```bash
   sudo ufw allow 5432/tcp
   ```

4. Restart PostgreSQL:
   ```bash
   sudo systemctl restart postgresql
   ```

**⚠️ Warning:** Be cautious when allowing remote access. Use strong passwords and consider VPN or SSH tunneling.

## Additional Resources

- [PostgreSQL Official Documentation](https://www.postgresql.org/docs/)
- [PostgreSQL Performance Tuning](https://wiki.postgresql.org/wiki/Performance_Optimization)
- [PostgreSQL Security](https://www.postgresql.org/docs/current/security.html)
