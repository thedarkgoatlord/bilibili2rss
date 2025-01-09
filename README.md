一个使用 RSS 订阅b站up主的小项目。主要实现方式是爬虫，可能不太优雅，部署详情见[这篇文章](https://blog.csdn.net/monochrome_/article/details/145031199?sharetype=blogdetail&sharerId=145031199&sharerefer=PC&sharesource=monochrome_&spm=1011.2480.3001.8118)。
最近的更新允许你一次订阅多位up主，只需要把up主的 UI D写入 UIDs.txt 中然后把 automator 的自动执行文件从 request.py 改为 multiple_requests.py 即可。

效果可以参考./output/中的几个 rss feed.
