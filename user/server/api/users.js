const express = require('express');
const router = express.Router();

router.post('/echo', (req, res) => {
    res.send(req.body);
});

module.exports = router;