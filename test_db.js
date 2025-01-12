const { Pool } = require('pg');
const { Client } = require('pg');

// 测试连接池
async function testPool() {
    const pool = new Pool({
        user: 'postgres',
        password: 'n9fh6pfn',
        host: 'dbconn.sealoshzh.site',
        port: 39066,
        database: 'postgres',
        ssl: {
            rejectUnauthorized: false
        },
        connectionTimeoutMillis: 5000
    });

    try {
        console.log('Testing connection with Pool...');
        const client = await pool.connect();
        const result = await client.query('SELECT NOW()');
        console.log('Pool connection successful!');
        console.log('Current time:', result.rows[0].now);
        client.release();
        await pool.end();
    } catch (err) {
        console.error('Pool connection error:', err);
    }
}

// 测试单个客户端连接
async function testClient() {
    const client = new Client({
        user: 'postgres',
        password: 'n9fh6pfn',
        host: 'dbconn.sealoshzh.site',
        port: 39066,
        database: 'postgres',
        ssl: {
            rejectUnauthorized: false
        }
    });

    try {
        console.log('\nTesting connection with Client...');
        await client.connect();
        const result = await client.query('SELECT NOW()');
        console.log('Client connection successful!');
        console.log('Current time:', result.rows[0].now);
        await client.end();
    } catch (err) {
        console.error('Client connection error:', err);
    }
}

// 运行测试
async function runTests() {
    await testPool();
    await new Promise(resolve => setTimeout(resolve, 1000)); // 等待1秒
    await testClient();
}

runTests(); 