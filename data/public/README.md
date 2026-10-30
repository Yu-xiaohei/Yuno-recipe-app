# 公共发布目录

本目录仅接收已审阅的canonical食谱、独立食材及引用图片。当前`catalog.json`为空bootstrap，不是正式上线内容；`data/reference`不会自动迁入这里。

维护`config/catalog-publication.json`，使用`python scripts/catalog_integrity.py build`生成目录，再用`verify`独立核验；提交前还须运行`verify --git-mode staged --baseline-ref HEAD`。

操作与失败处理见[哈希与上传校验](../../docs/公共食谱哈希与上传校验.md)。`contentHash`属于正文原始字节，正文不带自己的hash；独立库记录不按hash合并。
