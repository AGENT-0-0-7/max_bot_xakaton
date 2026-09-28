export const getWebApp = () => {
  if (typeof window === 'undefined') {
    return null;
  }
  return window.WebApp || null;
};

export const getMaxContext = () => {
  const app = getWebApp();
  if (!app) {
    return {
      isMax: false,
      initData: null,
      platform: 'browser',
      user: null,
      startParam: null,
    };
  }

  return {
    isMax: true,
    initData: app.initData || null,
    platform: app.platform || 'max',
    user: app.initDataUnsafe?.user || null,
    startParam: app.initDataUnsafe?.start_param || null,
  };
};

export const prepareMaxApp = () => {
  const app = getWebApp();
  if (!app) {
    return;
  }

  try {
    app.ready?.();
    app.expand?.();
    app.disableVerticalSwipes?.();
  } catch (error) {
    console.warn('MAX Bridge is available but could not prepare the view.', error);
  }
};

export const shareInMax = async (text) => {
  const app = getWebApp();
  const url = 'https://max.ru/:share?text=' + encodeURIComponent(text);

  if (app?.openMaxLink) {
    app.openMaxLink(url);
    return 'max';
  }

  if (navigator.clipboard?.writeText) {
    await navigator.clipboard.writeText(text);
    return 'clipboard';
  }

  return 'none';
};
