const { Pool } = require('pg');

const pool = new Pool({
    user: process.env.DATABASE_USER || 'postgres',
    password: process.env.DATABASE_PASSWORD || 'n9fh6pfn',
    host: process.env.DATABASE_HOST || 'dbconn.sealoshzh.site',
    port: process.env.DATABASE_PORT || 39066,
    database: process.env.DATABASE_NAME || 'postgres',
    ssl: {
        rejectUnauthorized: false
    }
});

module.exports = {
    query: (text, params) => pool.query(text, params),
    pool: pool
}; 