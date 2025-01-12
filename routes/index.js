const express = require('express');
const router = express.Router();
const db = require('../db');

router.get('/', async (req, res) => {
    try {
        const page = parseInt(req.query.page) || 1;
        const limit = 10;
        const offset = (page - 1) * limit;
        
        // 获取文章总数
        const countResult = await db.query('SELECT COUNT(*) FROM articles');
        const total = parseInt(countResult.rows[0].count);
        
        // 获取分页文章
        const result = await db.query(`
            SELECT a.*, j.name as journal_name 
            FROM articles a 
            LEFT JOIN journals j ON a.journal_id = j.id 
            ORDER BY a.published_date DESC 
            LIMIT $1 OFFSET $2
        `, [limit, offset]);

        // 修正这里：设置默认值为 true
        const isEnglish = true;  // 默认显示英文

        res.render('home', {
            articles: result.rows,
            isEnglish: isEnglish,
            pagination: {
                current: page,
                pages: Math.ceil(total / limit)
            }
        });
    } catch (err) {
        console.error('Error fetching articles:', err);
        res.status(500).send('Server Error');
    }
});

// 文章详情页路由
router.get('/articles/:id', async (req, res) => {
    try {
        // 获取文章信息
        const articleResult = await db.query(`
            SELECT a.*, j.name as journal_name 
            FROM articles a 
            LEFT JOIN journals j ON a.journal_id = j.id 
            WHERE a.id = $1
        `, [req.params.id]);

        if (articleResult.rows.length === 0) {
            return res.status(404).send('Article not found');
        }

        // 获取评论信息
        const commentsResult = await db.query(`
            SELECT c.*, u.username 
            FROM comments c 
            LEFT JOIN users u ON c.user_id = u.id 
            WHERE c.article_id = $1 
            ORDER BY c.created_at DESC
        `, [req.params.id]);

        const isEnglish = true;  // 默认显示英文

        res.render('article', {
            article: articleResult.rows[0],
            comments: commentsResult.rows,  // 添加评论数据
            isEnglish: isEnglish
        });
    } catch (err) {
        console.error('Error fetching article:', err);
        res.status(500).send('Server Error');
    }
});

// 添加评论的路由
router.post('/articles/:id/comments', async (req, res) => {
    try {
        // 验证评论内容
        if (!req.body.content || req.body.content.trim() === '') {
            return res.status(400).send('Comment content cannot be empty');
        }

        // 确保默认用户存在
        await db.query(`
            INSERT INTO users (id, username, email) 
            VALUES (1, 'anonymous', 'anonymous@example.com')
            ON CONFLICT (id) DO NOTHING
        `);

        // 添加评论
        await db.query(
            `INSERT INTO comments (article_id, user_id, content, created_at) 
             VALUES ($1, $2, $3, NOW())`,
            [req.params.id, 1, req.body.content.trim()]
        );

        res.redirect(`/articles/${req.params.id}`);
    } catch (err) {
        console.error('Error adding comment:', err);
        res.status(500).render('error', { 
            error: 'Failed to add comment. Please try again.' 
        });
    }
});

module.exports = router; 