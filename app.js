const express = require('express');
const cors = require('cors');
const { Pool } = require('pg');
const swaggerUi = require('swagger-ui-express');
const swaggerJsdoc = require('swagger-jsdoc');
const path = require('path');
const expressLayouts = require('express-ejs-layouts');
const cookieParser = require('cookie-parser');
require('dotenv').config();

// 创建 Express 应用
const app = express();
const port = process.env.PORT || 3000;

// 引入路由
const indexRouter = require('./routes/index');

// Swagger 配置
const swaggerOptions = {
  definition: {
    openapi: '3.0.0',
    info: {
      title: 'Articles API',
      version: '1.0.0',
      description: 'API documentation for Articles service',
    },
    servers: [
      {
        url: `http://localhost:${port}`,
        description: 'Development server',
      },
    ],
  },
  apis: ['./app.js'],
};

const swaggerSpec = swaggerJsdoc(swaggerOptions);
app.use('/api-docs', swaggerUi.serve, swaggerUi.setup(swaggerSpec));

// 创建数据库连接池
const pool = new Pool({
  user: process.env.DATABASE_USER,
  password: process.env.DATABASE_PASSWORD,
  host: process.env.DATABASE_HOST,
  port: process.env.DATABASE_PORT,
  database: process.env.DATABASE_NAME,
  ssl: {
    rejectUnauthorized: false
  },
  max: 20,
  idleTimeoutMillis: 30000,
  connectionTimeoutMillis: 10000,
  retry_strategy: {
    retries: 3,
    factor: 2,
    minTimeout: 1000,
    maxTimeout: 5000
  }
});

// 添加连接错误处理
pool.on('error', (err) => {
  console.error('Unexpected error on idle client', err);
});

// 中间件
app.use(cors());
app.use(express.urlencoded({ extended: true }));
app.use(express.json());
app.use(cookieParser());

// 设置模板引擎
app.set('view engine', 'ejs');
app.set('views', path.join(__dirname, 'views'));
app.use(expressLayouts);
app.use(express.static(path.join(__dirname, 'public')));

// 使用路由
app.use('/', indexRouter);

// 基础路由
/**
 * @swagger
 * /api/health:
 *   get:
 *     summary: 健康检查端点
 *     description: 用于检查API服务是否正常运行
 *     responses:
 *       200:
 *         description: 服务正常运行
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 status:
 *                   type: string
 *                   example: ok
 */
app.get('/api/health', (req, res) => {
  res.json({ status: 'ok' });
});

/**
 * @swagger
 * /api/articles:
 *   get:
 *     summary: 获取文章列表
 *     description: 返回分页的文章列表
 *     parameters:
 *       - in: query
 *         name: page
 *         schema:
 *           type: integer
 *         description: 页码（默认：1）
 *       - in: query
 *         name: limit
 *         schema:
 *           type: integer
 *         description: 每页数量（默认：10）
 *     responses:
 *       200:
 *         description: 成功返回文章列表
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 data:
 *                   type: array
 *                   items:
 *                     type: object
 *                     properties:
 *                       id:
 *                         type: integer
 *                       title:
 *                         type: string
 *                       journal_name:
 *                         type: string
 *                 pagination:
 *                   type: object
 *                   properties:
 *                     current_page:
 *                       type: integer
 *                     per_page:
 *                       type: integer
 *                     total:
 *                       type: integer
 *       500:
 *         description: 服务器错误
 */
app.get('/api/articles', async (req, res) => {
  try {
    const page = parseInt(req.query.page) || 1;
    const limit = parseInt(req.query.limit) || 10;
    const offset = (page - 1) * limit;

    const articles = await pool.query(
      `SELECT a.*, j.name as journal_name 
       FROM articles a 
       LEFT JOIN journals j ON a.journal_id = j.id 
       ORDER BY a.published_date DESC 
       LIMIT $1 OFFSET $2`,
      [limit, offset]
    );

    const total = await pool.query('SELECT COUNT(*) as count FROM articles');

    res.json({
      data: articles.rows,
      pagination: {
        current_page: page,
        per_page: limit,
        total: parseInt(total.rows[0].count)
      }
    });
  } catch (error) {
    console.error('Error fetching articles:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

/**
 * @swagger
 * /api/articles/{id}:
 *   get:
 *     summary: 获取单个文章详情
 *     parameters:
 *       - in: path
 *         name: id
 *         required: true
 *         schema:
 *           type: integer
 *         description: 文章ID
 *     responses:
 *       200:
 *         description: 成功返回文章详情
 *       404:
 *         description: 文章未找到
 *       500:
 *         description: 服务器错误
 */
app.get('/api/articles/:id', async (req, res) => {
  try {
    const article = await pool.query(
      `SELECT a.*, j.name as journal_name 
       FROM articles a 
       LEFT JOIN journals j ON a.journal_id = j.id 
       WHERE a.id = $1`,
      [req.params.id]
    );

    if (article.rows.length === 0) {
      return res.status(404).json({ error: 'Article not found' });
    }

    // 获取文章的标签
    const tags = await pool.query(
      `SELECT t.name 
       FROM tags t 
       JOIN article_tags at ON t.id = at.tag_id 
       WHERE at.article_id = $1`,
      [req.params.id]
    );

    article.rows[0].tags = tags.rows.map(tag => tag.name);

    res.json(article.rows[0]);
  } catch (error) {
    console.error('Error fetching article:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

/**
 * @swagger
 * /api/journals/{journalId}/articles:
 *   get:
 *     summary: 获取特定期刊的文章
 *     parameters:
 *       - in: path
 *         name: journalId
 *         required: true
 *         schema:
 *           type: integer
 *         description: 期刊ID
 *       - in: query
 *         name: page
 *         schema:
 *           type: integer
 *         description: 页码（默认：1）
 *       - in: query
 *         name: limit
 *         schema:
 *           type: integer
 *         description: 每页数量（默认：10）
 *     responses:
 *       200:
 *         description: 成功返回期刊文章列表
 *       500:
 *         description: 服务器错误
 */
app.get('/api/journals/:journalId/articles', async (req, res) => {
  try {
    const page = parseInt(req.query.page) || 1;
    const limit = parseInt(req.query.limit) || 10;
    const offset = (page - 1) * limit;

    const articles = await pool.query(
      `SELECT a.*, j.name as journal_name 
       FROM articles a 
       LEFT JOIN journals j ON a.journal_id = j.id 
       WHERE j.id = $1 
       ORDER BY a.published_date DESC 
       LIMIT $2 OFFSET $3`,
      [req.params.journalId, limit, offset]
    );

    const total = await pool.query(
      'SELECT COUNT(*) as count FROM articles WHERE journal_id = $1',
      [req.params.journalId]
    );

    res.json({
      data: articles.rows,
      pagination: {
        current_page: page,
        per_page: limit,
        total: parseInt(total.rows[0].count)
      }
    });
  } catch (error) {
    console.error('Error fetching journal articles:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

async function testConnection() {
  let retries = 3;
  while (retries > 0) {
    try {
      console.log(`Attempting to connect to database... (${retries} retries left)`);
      const client = await pool.connect();
      const result = await client.query('SELECT NOW()');
      console.log('Database connection successful');
      console.log('Current database time:', result.rows[0]);
      client.release();
      return;
    } catch (err) {
      retries--;
      console.error('Database connection error:', {
        message: err.message,
        code: err.code,
        stack: err.stack
      });
      if (retries > 0) {
        console.log('Retrying in 2 seconds...');
        await new Promise(resolve => setTimeout(resolve, 2000));
      }
    }
  }
}

app.listen(port, async () => {
  await testConnection();
  console.log(`Server running on port ${port}`);
});

// 添加前端路由
app.get('/', async (req, res) => {
  try {
    const page = parseInt(req.query.page) || 1;
    const limit = parseInt(req.query.limit) || 12;
    const offset = (page - 1) * limit;

    const articles = await pool.query(
      `SELECT a.*, j.name as journal_name 
       FROM articles a 
       LEFT JOIN journals j ON a.journal_id = j.id 
       ORDER BY a.published_date DESC 
       LIMIT $1 OFFSET $2`,
      [limit, offset]
    );

    const total = await pool.query('SELECT COUNT(*) as count FROM articles');

    res.render('home', {
      articles: articles.rows,
      pagination: {
        current: page,
        pages: Math.ceil(total.rows[0].count / limit)
      }
    });
  } catch (error) {
    console.error('Error:', error);
    res.status(500).render('error', { error: 'Internal server error' });
  }
});

// 文章详情页面路由
app.get('/articles/:id', async (req, res) => {
    try {
        const article = await pool.query(
            `SELECT a.*, j.name as journal_name 
             FROM articles a 
             LEFT JOIN journals j ON a.journal_id = j.id 
             WHERE a.id = $1`,
            [req.params.id]
        );

        const comments = await pool.query(
            `SELECT c.*, u.username 
             FROM comments c 
             LEFT JOIN users u ON c.user_id = u.id 
             WHERE c.article_id = $1 
             ORDER BY c.created_at DESC`,
            [req.params.id]
        );

        if (article.rows.length === 0) {
            return res.status(404).render('error', { error: 'Article not found' });
        }

        res.render('article', {
            article: article.rows[0],
            comments: comments.rows
        });
    } catch (error) {
        console.error('Error:', error);
        res.status(500).render('error', { error: 'Internal server error' });
    }
});

// 添加评论的路由
app.post('/articles/:id/comments', async (req, res) => {
    const client = await pool.connect();
    
    try {
        // 验证评论内容
        if (!req.body.content || req.body.content.trim() === '') {
            return res.status(400).render('error', { 
                error: 'Comment content cannot be empty' 
            });
        }

        await client.query('BEGIN'); // 开始事务

        // 确保用户存在，如果不存在则创建
        const userResult = await client.query(
            'INSERT INTO users (id, username, email) VALUES (1, \'anonymous\', \'anonymous@example.com\') ON CONFLICT (id) DO NOTHING RETURNING id'
        );

        // 添加评论
        await client.query(
            `INSERT INTO comments (article_id, user_id, content, created_at) 
             VALUES ($1, $2, $3, NOW())`,
            [req.params.id, 1, req.body.content.trim()]
        );

        await client.query('COMMIT');
        res.redirect(`/articles/${req.params.id}`);
    } catch (error) {
        await client.query('ROLLBACK');
        console.error('Error:', error);
        res.status(500).render('error', { 
            error: 'Failed to add comment. Please try again.' 
        });
    } finally {
        client.release();
    }
});

