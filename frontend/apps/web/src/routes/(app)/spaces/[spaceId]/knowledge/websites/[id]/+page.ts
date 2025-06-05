export const load = async (event) => {
  const { intric } = await event.parent();

  // Load website and info blobs only once
  const [website, infoBlobs] = await Promise.all([
    intric.websites.get({ id: event.params.id }),
    intric.websites.indexedBlobs.list({ id: event.params.id })
  ]);

  // Load crawl runs separately with dependency tracking
  event.depends("crawlruns:list");
  const crawlRuns = await intric.websites.crawlRuns.list({ id: event.params.id });

  return {
    crawlRuns: crawlRuns.reverse(),
    infoBlobs,
    website
  };
};
