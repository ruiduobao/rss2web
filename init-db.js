const db = require('./db');

async function initDatabase() {
    try {
        // 创建用户表
        await db.query(`
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(100) NOT NULL,
                email VARCHAR(255)
            );
        `);

        // 创建评论表
        await db.query(`
            CREATE TABLE IF NOT EXISTS comments (
                id SERIAL PRIMARY KEY,
                article_id INTEGER REFERENCES articles(id),
                user_id INTEGER REFERENCES users(id),
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        `);

        // 添加默认匿名用户
        await db.query(`
            INSERT INTO users (id, username, email) 
            VALUES (1, 'anonymous', 'anonymous@example.com')
            ON CONFLICT (id) DO NOTHING;
        `);

        console.log('Database initialized successfully');
    } catch (err) {
        console.error('Error initializing database:', err);
    } finally {
        // 关闭数据库连接
        db.pool.end();
    }
}

initDatabase(); 