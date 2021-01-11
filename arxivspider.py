import scrapy
from scrapy.crawler import CrawlerProcess
import csv


HEADING = [
    'A/C', 'Year', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'
    ]

class ArxivSpider(scrapy.Spider):
    name = 'arxiv'
    custom_settings = {
        'CONCURRENT_REQUEST_PER_DOMAIN': 1,
        'DOWNLOAD_DELAY': 5
    }
    start_urls = "https://arxiv.org/"
    headers = {
        'User_Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.183 Safari/537.36 RuxitSynthetic/1.0 v8134650122 t38550 ath9b965f92 altpub cvcv=2'
    }

    def start_requests(self):
        yield scrapy.Request(self.start_urls, callback=self.parse, headers=self.headers)

    def parse(self, response, **kwargs):
        section = response.xpath("//div[@id='content']/h2/following-sibling::ul/li/a[1]/text()").getall()
        nextlinks = response.xpath("//div[@id='content']/h2/following-sibling::ul/li/a[1]/@href").getall()

        unwanted = [24, 23, 22, 21, 20, 14]
        for element in unwanted:
            del section[element]
            del nextlinks[element] #remove computer science link

        print(section)

        for i in range(len(nextlinks)):
            filename = './output/' + f'{section[i]}.csv'
            with open(filename, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['#Article Statistics for ' + section[i]])
                writer.writerow(HEADING)
            yield response.follow(nextlinks[i], self.segmentparse, cb_kwargs=dict(filename=filename))

    def segmentparse(self, response, filename):
        nextlinks = response.xpath("//div[@id='content']/ul[1]/li[4]/a/@href").getall()
        years = response.xpath("//div[@id='content']/ul[1]/li[4]/a/text()").getall()
        del nextlinks[0]
        del years[0]
        for i in range(len(years)):
            yield response.follow(nextlinks[i], self.scrapestat,
                                  cb_kwargs=dict(filename=filename, year=years[i]))

    def scrapestat(self, response, filename, year):
        articles = response.xpath("//div[@id='content']//li/b/text()").getall()
        crosslistings = response.xpath("//div[@id='content']//li/i/text()").getall()

        #make up to 12 months
        if len(articles) < 12:
            articles = (12 - len(articles)) * [None] + articles
            crosslistings = (12 - len(crosslistings)) * [None] + crosslistings

        articles = ['Articles', year] + articles
        crosslistings = ['Crosslistings', year] + crosslistings

        data = [articles, crosslistings]

        with open(filename, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerows(data)


if __name__ == '__main__':
    process = CrawlerProcess()
    process.crawl(ArxivSpider)
    process.start()
