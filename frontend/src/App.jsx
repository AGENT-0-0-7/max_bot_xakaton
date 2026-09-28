import React, { useCallback, useEffect, useMemo, useState } from 'react';

import {
  getMaxContext,
  shareInMax,
} from './maxBridge';

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/$/, '');
const DEMO_MODE = import.meta.env.VITE_DEMO_MODE === 'true';
const DEFAULT_COORDS = { latitude: 57.153033, longitude: 65.534328 };

const CATEGORIES = {
  all: { label: 'Все', icon: '✦' },
  sport: { label: 'Спорт', icon: '⚡' },
  education: { label: 'Учусь', icon: '⌁' },
  culture: { label: 'Культура', icon: '◌' },
  party: { label: 'Встречи', icon: '☀' },
  volunteering: { label: 'Помощь', icon: '♡' },
};

const STATUS_LABELS = {
  pending: 'На модерации',
  approved: 'Опубликовано',
  rejected: 'Отклонено',
  cancelled: 'Отменено',
};

const toInputValue = (date) => {
  const value = new Date(date);
  value.setMinutes(value.getMinutes() - value.getTimezoneOffset());
  return value.toISOString().slice(0, 16);
};

const emptyForm = (location = DEFAULT_COORDS) => ({
  title: '',
  description: '',
  category: 'culture',
  address: '',
  latitude: location.latitude,
  longitude: location.longitude,
  start_time: toInputValue(Date.now() + 1000 * 60 * 60 * 24),
  end_time: toInputValue(Date.now() + 1000 * 60 * 60 * 26),
  max_participants: 20,
});

const formatDate = (value) =>
  new Intl.DateTimeFormat('ru-RU', {
    weekday: 'short',
    day: 'numeric',
    month: 'long',
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(value));

const formatDistance = (meters) => {
  if (meters === null || meters === undefined) {
    return 'Рядом';
  }
  if (meters < 1000) {
    return meters + ' м';
  }
  return (meters / 1000).toFixed(meters < 10000 ? 1 : 0) + ' км';
};

const getErrorMessage = (payload, fallback) => {
  if (!payload) {
    return fallback;
  }
  if (typeof payload.detail === 'string') {
    return payload.detail;
  }
  if (typeof payload.message === 'string') {
    return payload.message;
  }
  const values = Object.values(payload)
    .flat()
    .filter((item) => typeof item === 'string');
  return values[0] || fallback;
};

const api = async (path, options = {}) => {
  const response = await fetch(API_BASE_URL + path, {
    ...options,
    headers: {
      Accept: 'application/json',
      ...(options.headers || {}),
    },
  });
  const payload = await response.json().catch(() => null);
  if (!response.ok) {
    const error = new Error(getErrorMessage(payload, 'Сервис временно недоступен.'));
    error.payload = payload;
    throw error;
  }
  return payload;
};

const demoInitData = () => {
  let demoId = null;
  try {
    demoId = window.localStorage.getItem('ryadom_demo_user_id');
    if (!demoId || !/^\d+$/.test(demoId)) {
      const random = new Uint32Array(1);
      window.crypto.getRandomValues(random);
      demoId = String(900000 + (random[0] % 1000000000));
      window.localStorage.setItem('ryadom_demo_user_id', demoId);
    }
  } catch {
    demoId = String(900000 + (Date.now() % 1000000000));
  }
  const user = {
    id: Number(demoId),
    first_name: 'Гость',
    last_name: 'Демо',
    username: 'max_demo_user',
  };
  return (
    'user=' +
    encodeURIComponent(JSON.stringify(user)) +
    '&auth_date=' +
    Math.floor(Date.now() / 1000) +
    '&hash=mock_hash'
  );
};

const authHeaders = (token) =>
  token ? { Authorization: 'Bearer ' + token } : {};

function EventCard({ event, selected, onSelect }) {
  const category = CATEGORIES[event.category] || CATEGORIES.culture;
  return (
    <button
      className={'event-card' + (selected ? ' selected' : '')}
      type="button"
      onClick={() => onSelect(event.id)}
    >
      <div className="event-card-top">
        <span className="category-pill">
          <span aria-hidden="true">{category.icon}</span> {category.label}
        </span>
        <span className="distance">{formatDistance(event.distance_meters)}</span>
      </div>
      <h3>{event.title}</h3>
      <p className="event-date">{formatDate(event.start_time)}</p>
      <p className="event-address">{event.address}</p>
      <div className="event-card-bottom">
        <span>{event.available_seats} мест</span>
        {event.is_registered && <span className="registered-mark">Вы идёте</span>}
      </div>
    </button>
  );
}

function EventDetails({
  event,
  canJoin,
  isBusy,
  onJoin,
  onCancel,
  onShare,
}) {
  if (!event) {
    return (
      <aside className="event-details empty-details">
        <span className="empty-icon">⌖</span>
        <h2>Выберите событие</h2>
        <p>Откройте карточку, чтобы узнать детали и сразу записаться.</p>
      </aside>
    );
  }

  const category = CATEGORIES[event.category] || CATEGORIES.culture;
  const isSoldOut = event.available_seats <= 0 && !event.is_registered;

  return (
    <aside className="event-details">
      <div className="detail-topline">
        <span className="category-pill">
          <span aria-hidden="true">{category.icon}</span> {category.label}
        </span>
        <button
          className="icon-button"
          type="button"
          aria-label="Поделиться событием"
          onClick={onShare}
        >
          ↗
        </button>
      </div>
      <h2>{event.title}</h2>
      <p className="detail-description">{event.description}</p>

      <dl className="details-list">
        <div>
          <dt>Когда</dt>
          <dd>{formatDate(event.start_time)}</dd>
        </div>
        <div>
          <dt>Где</dt>
          <dd>{event.address}</dd>
        </div>
        <div>
          <dt>Расстояние</dt>
          <dd>{formatDistance(event.distance_meters)} от вас</dd>
        </div>
        <div>
          <dt>Места</dt>
          <dd>{event.available_seats} из {event.max_participants} свободно</dd>
        </div>
      </dl>

      {event.is_registered ? (
        <div className="registered-action">
          <div>
            <strong>Вы записаны</strong>
            <span>Запись сохранена в личном кабинете.</span>
          </div>
          <button
            className="text-button danger"
            type="button"
            onClick={onCancel}
            disabled={isBusy}
          >
            Отменить
          </button>
        </div>
      ) : (
        <button
          className="primary-button full-button"
          type="button"
          onClick={onJoin}
          disabled={!canJoin || isSoldOut || isBusy}
        >
          {isBusy ? 'Проверяем места…' : isSoldOut ? 'Мест не осталось' : 'Записаться'}
        </button>
      )}
    </aside>
  );
}

function CreateEventForm({ formData, onChange, onSubmit, onUseLocation, busy }) {
  return (
    <section className="creator-card">
      <div className="section-heading">
        <div>
          <span className="section-kicker">Организатор</span>
          <h2>Новое событие</h2>
        </div>
        <p>После проверки модератором событие появится в общей ленте.</p>
      </div>
      <form onSubmit={onSubmit}>
        <div className="form-grid">
          <label className="full-span">
            Название
            <input
              value={formData.title}
              onChange={onChange('title')}
              placeholder="Например, вечер настольных игр"
              maxLength="255"
              required
            />
          </label>
          <label>
            Категория
            <select value={formData.category} onChange={onChange('category')}>
              {Object.entries(CATEGORIES)
                .filter(([key]) => key !== 'all')
                .map(([key, category]) => (
                  <option key={key} value={key}>{category.label}</option>
                ))}
            </select>
          </label>
          <label>
            Лимит участников
            <input
              type="number"
              min="1"
              max="500"
              value={formData.max_participants}
              onChange={onChange('max_participants')}
              required
            />
          </label>
          <label className="full-span">
            Описание
            <textarea
              value={formData.description}
              onChange={onChange('description')}
              placeholder="Что будет происходить и кому подойдёт событие?"
              rows="4"
              required
            />
          </label>
          <label className="full-span">
            Адрес
            <input
              value={formData.address}
              onChange={onChange('address')}
              placeholder="Улица, дом или понятная точка встречи"
              maxLength="255"
              required
            />
          </label>
          <label>
            Начало
            <input
              type="datetime-local"
              value={formData.start_time}
              onChange={onChange('start_time')}
              required
            />
          </label>
          <label>
            Окончание
            <input
              type="datetime-local"
              value={formData.end_time}
              onChange={onChange('end_time')}
              required
            />
          </label>
          <label>
            Широта
            <input
              type="number"
              step="0.000001"
              min="-90"
              max="90"
              value={formData.latitude}
              onChange={onChange('latitude')}
              required
            />
          </label>
          <label>
            Долгота
            <input
              type="number"
              step="0.000001"
              min="-180"
              max="180"
              value={formData.longitude}
              onChange={onChange('longitude')}
              required
            />
          </label>
        </div>
        <div className="form-actions">
          <button className="secondary-button" type="button" onClick={onUseLocation}>
            Использовать мою геолокацию
          </button>
          <button className="primary-button" type="submit" disabled={busy}>
            {busy ? 'Отправляем…' : 'Отправить на модерацию'}
          </button>
        </div>
      </form>
    </section>
  );
}

export default function App() {
  const [maxContext, setMaxContext] = useState({
    isMax: false,
    platform: 'browser',
    user: null,
  });
  const [authToken, setAuthToken] = useState(null);
  const [currentUser, setCurrentUser] = useState(null);
  const [events, setEvents] = useState([]);
  const [registrations, setRegistrations] = useState([]);
  const [organizerEvents, setOrganizerEvents] = useState([]);
  const [location, setLocation] = useState(DEFAULT_COORDS);
  const [selectedId, setSelectedId] = useState(null);
  const [activeTab, setActiveTab] = useState('discover');
  const [category, setCategory] = useState('all');
  const [freeOnly, setFreeOnly] = useState(false);
  const [isLoadingEvents, setIsLoadingEvents] = useState(true);
  const [isAccountLoading, setIsAccountLoading] = useState(false);
  const [isActionBusy, setIsActionBusy] = useState(false);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [formData, setFormData] = useState(emptyForm());
  const [notice, setNotice] = useState(null);

  const refreshEvents = useCallback(async () => {
    setIsLoadingEvents(true);
    try {
      const params = new URLSearchParams({
        lat: String(location.latitude),
        lon: String(location.longitude),
        radius_km: '25',
      });
      const data = await api('/api/v1/events/?' + params.toString(), {
        headers: authHeaders(authToken),
      });
      setEvents(data);
      setSelectedId((previous) => {
        if (previous && data.some((event) => event.id === previous)) {
          return previous;
        }
        return data[0]?.id || null;
      });
    } catch (error) {
      setEvents([]);
      setSelectedId(null);
      setNotice({
        type: 'error',
        text: getErrorMessage(error.payload, 'Не удалось загрузить события. Попробуйте ещё раз.'),
      });
    } finally {
      setIsLoadingEvents(false);
    }
  }, [authToken, location]);

  const refreshAccount = useCallback(async () => {
    if (!authToken) {
      setRegistrations([]);
      setOrganizerEvents([]);
      return;
    }
    setIsAccountLoading(true);
    try {
      const headers = authHeaders(authToken);
      const data = await Promise.all([
        api('/api/v1/users/me/registrations/', { headers }),
        api('/api/v1/users/me/events/', { headers }),
      ]);
      setRegistrations(data[0]);
      setOrganizerEvents(data[1]);
    } catch (error) {
      setNotice({
        type: 'error',
        text: 'Не удалось обновить личный кабинет. Повторите действие.',
      });
    } finally {
      setIsAccountLoading(false);
    }
  }, [authToken]);

  useEffect(() => {
    const bootstrap = async () => {
      const context = getMaxContext();
      setMaxContext(context);
      if (!context.initData && (context.isMax || !DEMO_MODE)) {
        setNotice({
          type: 'error',
          text: context.isMax
            ? 'MAX не передал данные запуска. Закройте мини-приложение и откройте его снова из чата с ботом.'
            : 'Демо-вход выключен. Запустите стенд через Docker в демо-режиме или откройте приложение из MAX.',
        });
        return;
      }
      try {
        const data = await api('/api/v1/auth/max/', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            init_data: context.initData || demoInitData(),
          }),
        });
        setAuthToken(data.access_token);
        setCurrentUser(data.user);
      } catch (error) {
        setNotice({
          type: 'error',
          text: 'Не удалось подтвердить вход через MAX. Проверьте настройки сервера.',
        });
      }
    };
    bootstrap();
  }, []);

  useEffect(() => {
    refreshEvents();
  }, [refreshEvents]);

  useEffect(() => {
    refreshAccount();
  }, [refreshAccount]);

  const filteredEvents = useMemo(
    () =>
      events.filter((event) => {
        const categoryMatches = category === 'all' || event.category === category;
        const seatsMatch = !freeOnly || event.available_seats > 0;
        return categoryMatches && seatsMatch;
      }),
    [category, events, freeOnly],
  );

  const selectedEvent =
    filteredEvents.find((event) => event.id === selectedId) ||
    events.find((event) => event.id === selectedId) ||
    null;

  const useMyLocation = (successMessage) => {
    if (!navigator.geolocation) {
      setNotice({ type: 'error', text: 'Геолокация не поддерживается этим устройством.' });
      return;
    }
    navigator.geolocation.getCurrentPosition(
      (position) => {
        const nextLocation = {
          latitude: position.coords.latitude,
          longitude: position.coords.longitude,
        };
        setLocation(nextLocation);
        setFormData((previous) => ({
          ...previous,
          latitude: nextLocation.latitude,
          longitude: nextLocation.longitude,
        }));
        setNotice({ type: 'success', text: successMessage });
      },
      () => {
        setNotice({
          type: 'error',
          text: 'Не удалось получить геолокацию. Используем точку по умолчанию.',
        });
      },
      { enableHighAccuracy: true, timeout: 10000, maximumAge: 300000 },
    );
  };

  const handleJoin = async () => {
    if (!selectedEvent || !authToken) {
      setNotice({ type: 'error', text: 'Сначала подтвердите вход через MAX.' });
      return;
    }
    setIsActionBusy(true);
    try {
      const result = await api('/api/v1/events/' + selectedEvent.id + '/register/', {
        method: 'POST',
        headers: authHeaders(authToken),
      });
      setNotice({
        type: 'success',
        text: result.notification_sent
          ? 'Готово! Вы записаны, подтверждение отправлено в чат с ботом MAX.'
          : 'Вы записаны. Уведомление MAX недоступно; событие сохранено в «Мои планы».',
      });
      await Promise.all([refreshEvents(), refreshAccount()]);
    } catch (error) {
      setNotice({
        type: 'error',
        text: getErrorMessage(error.payload, 'Не удалось записаться на событие.'),
      });
    } finally {
      setIsActionBusy(false);
    }
  };

  const handleCancelRegistration = async (eventId) => {
    if (!authToken) {
      return;
    }
    setIsActionBusy(true);
    try {
      await api('/api/v1/events/' + eventId + '/registration/', {
        method: 'DELETE',
        headers: authHeaders(authToken),
      });
      setNotice({ type: 'success', text: 'Запись отменена, место снова доступно другим.' });
      await Promise.all([refreshEvents(), refreshAccount()]);
    } catch (error) {
      setNotice({
        type: 'error',
        text: getErrorMessage(error.payload, 'Не удалось отменить запись.'),
      });
    } finally {
      setIsActionBusy(false);
    }
  };

  const handleCancelEvent = async (eventId) => {
    if (!authToken) {
      return;
    }
    setIsActionBusy(true);
    try {
      await api('/api/v1/events/' + eventId + '/cancel/', {
        method: 'POST',
        headers: authHeaders(authToken),
      });
      setNotice({ type: 'success', text: 'Событие отменено.' });
      await Promise.all([refreshEvents(), refreshAccount()]);
    } catch (error) {
      setNotice({
        type: 'error',
        text: getErrorMessage(error.payload, 'Не удалось отменить событие.'),
      });
    } finally {
      setIsActionBusy(false);
    }
  };

  const handleShare = async () => {
    if (!selectedEvent) {
      return;
    }
    const text = 'Пойдём на «' + selectedEvent.title + '»? ' +
      formatDate(selectedEvent.start_time) + ', ' + selectedEvent.address;
    try {
      const result = await shareInMax(text);
      setNotice({
        type: 'success',
        text: result === 'clipboard'
          ? 'Текст приглашения скопирован.'
          : 'Открылся выбор чата для приглашения.',
      });
    } catch (error) {
      setNotice({ type: 'error', text: 'Не удалось подготовить приглашение.' });
    }
  };

  const handleFormChange = (field) => (event) => {
    const numericFields = ['latitude', 'longitude', 'max_participants'];
    const value = numericFields.includes(field)
      ? Number(event.target.value)
      : event.target.value;
    setFormData((previous) => ({ ...previous, [field]: value }));
  };

  const handleCreateEvent = async (event) => {
    event.preventDefault();
    if (!authToken) {
      setNotice({ type: 'error', text: 'Авторизация через MAX не завершена.' });
      return;
    }
    if (new Date(formData.end_time) <= new Date(formData.start_time)) {
      setNotice({ type: 'error', text: 'Время окончания должно быть позже времени начала.' });
      return;
    }

    setIsActionBusy(true);
    try {
      await api('/api/v1/events/', {
        method: 'POST',
        headers: {
          ...authHeaders(authToken),
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          ...formData,
          start_time: new Date(formData.start_time).toISOString(),
          end_time: new Date(formData.end_time).toISOString(),
        }),
      });
      setFormData(emptyForm(location));
      setShowCreateForm(false);
      setActiveTab('organizer');
      setNotice({
        type: 'success',
        text: 'Событие отправлено на модерацию. Статус виден во вкладке «Организую».',
      });
      await refreshAccount();
    } catch (error) {
      setNotice({
        type: 'error',
        text: getErrorMessage(error.payload, 'Не удалось создать событие.'),
      });
    } finally {
      setIsActionBusy(false);
    }
  };

  const openCreate = () => {
    setActiveTab('organizer');
    setShowCreateForm(true);
    setFormData(emptyForm(location));
  };

  return (
    <div className="app-shell">
      <header className="app-header">
        <button
          className="brand"
          type="button"
          onClick={() => setActiveTab('discover')}
          aria-label="Открыть события"
        >
          <span className="brand-mark">●</span>
          <span>Рядом</span>
        </button>
        <div className="header-actions">
          <span className="profile-chip">
            <span className="avatar">{(currentUser?.first_name || 'Г').slice(0, 1)}</span>
            <span>{currentUser?.first_name || 'Подключаем MAX…'}</span>
          </span>
          <button className="primary-button compact" type="button" onClick={openCreate}>
            <span aria-hidden="true">＋</span> Создать
          </button>
        </div>
      </header>

      {!maxContext.isMax && DEMO_MODE && (
        <div className="demo-banner">
          <span>Демо-режим</span>
          <p>Вы открыли стенд в браузере. В MAX вход и уведомления подтверждаются настоящими данными Bridge.</p>
        </div>
      )}

      {notice && (
        <div className={'notice ' + notice.type} role="status">
          <span>{notice.type === 'success' ? '✓' : '!'}</span>
          <p>{notice.text}</p>
          <button type="button" onClick={() => setNotice(null)} aria-label="Закрыть уведомление">×</button>
        </div>
      )}

      <nav className="tabbar" aria-label="Основная навигация">
        <button
          className={activeTab === 'discover' ? 'active' : ''}
          type="button"
          onClick={() => setActiveTab('discover')}
        >
          <span>⌖</span> События
        </button>
        <button
          className={activeTab === 'plans' ? 'active' : ''}
          type="button"
          onClick={() => setActiveTab('plans')}
        >
          <span>◷</span> Мои планы
        </button>
        <button
          className={activeTab === 'organizer' ? 'active' : ''}
          type="button"
          onClick={() => setActiveTab('organizer')}
        >
          <span>✦</span> Организую
        </button>
      </nav>

      {activeTab === 'discover' && (
        <>
          <section className="hero">
            <div>
              <span className="section-kicker">Досуг рядом с вами</span>
              <h1>Сегодня есть куда пойти.</h1>
              <p>Выбирайте локальные события, записывайтесь в один шаг и получайте детали в MAX.</p>
            </div>
            <button
              className="location-button"
              type="button"
              onClick={() => useMyLocation('Геолокация обновлена. Показываем события в радиусе 25 км.')}
            >
              <span>⌖</span>
              <span><small>Показываем рядом</small>До 25 км</span>
            </button>
          </section>

          <section className="filters" aria-label="Фильтры событий">
            <div className="category-row">
              {Object.entries(CATEGORIES).map(([key, item]) => (
                <button
                  className={'filter-chip' + (category === key ? ' active' : '')}
                  key={key}
                  type="button"
                  onClick={() => setCategory(key)}
                >
                  <span>{item.icon}</span> {item.label}
                </button>
              ))}
            </div>
            <label className="switch">
              <input
                type="checkbox"
                checked={freeOnly}
                onChange={() => setFreeOnly((value) => !value)}
              />
              <span />
              Только со свободными местами
            </label>
          </section>

          <main className="discover-layout">
            <section className="events-column">
              <div className="list-heading">
                <div>
                  <h2>Ближайшие события</h2>
                  <p>{isLoadingEvents ? 'Обновляем список…' : filteredEvents.length + ' вариантов для вас'}</p>
                </div>
                <button className="text-button" type="button" onClick={refreshEvents}>
                  Обновить
                </button>
              </div>
              <div className="event-list">
                {isLoadingEvents && <div className="loading-card">Ищем события рядом…</div>}
                {!isLoadingEvents && filteredEvents.length === 0 && (
                  <div className="empty-list">
                    <span>⌁</span>
                    <h3>Ничего не нашлось</h3>
                    <p>Снимите фильтр или попробуйте обновить геолокацию.</p>
                  </div>
                )}
                {!isLoadingEvents && filteredEvents.map((event) => (
                  <EventCard
                    event={event}
                    key={event.id}
                    selected={event.id === selectedEvent?.id}
                    onSelect={setSelectedId}
                  />
                ))}
              </div>
            </section>
            <EventDetails
              event={selectedEvent}
              canJoin={Boolean(authToken)}
              isBusy={isActionBusy}
              onJoin={handleJoin}
              onCancel={() => handleCancelRegistration(selectedEvent?.id)}
              onShare={handleShare}
            />
          </main>
        </>
      )}

      {activeTab === 'plans' && (
        <section className="account-page">
          <div className="section-heading">
            <div>
              <span className="section-kicker">Личный кабинет</span>
              <h1>Мои планы</h1>
            </div>
            <p>Все подтверждённые записи собраны здесь. Напоминание придёт в диалог с ботом.</p>
          </div>
          {isAccountLoading && <div className="loading-card">Загружаем ваши планы…</div>}
          {!isAccountLoading && registrations.length === 0 && (
            <div className="empty-list spacious">
              <span>◷</span>
              <h3>Планов пока нет</h3>
              <p>Выберите событие в ленте, чтобы оно появилось здесь.</p>
              <button className="primary-button" type="button" onClick={() => setActiveTab('discover')}>
                Найти событие
              </button>
            </div>
          )}
          <div className="account-grid">
            {registrations.map((registration) => (
              <article className="plan-card" key={registration.id}>
                <span className="plan-date">{formatDate(registration.start_time)}</span>
                <h2>{registration.title}</h2>
                <p>{registration.address}</p>
                <div className="plan-footer">
                  <span className="status-pill approved">Запись подтверждена</span>
                  <button
                    className="text-button danger"
                    type="button"
                    onClick={() => handleCancelRegistration(registration.event_id)}
                    disabled={isActionBusy}
                  >
                    Отменить
                  </button>
                </div>
              </article>
            ))}
          </div>
        </section>
      )}

      {activeTab === 'organizer' && (
        <section className="account-page">
          <div className="section-heading organizer-heading">
            <div>
              <span className="section-kicker">Организатор</span>
              <h1>Мои события</h1>
            </div>
            <button className="primary-button" type="button" onClick={openCreate}>
              ＋ Добавить событие
            </button>
          </div>
          {showCreateForm && (
            <CreateEventForm
              formData={formData}
              onChange={handleFormChange}
              onSubmit={handleCreateEvent}
              onUseLocation={() => useMyLocation('Координаты для нового события обновлены.')}
              busy={isActionBusy}
            />
          )}
          {isAccountLoading && <div className="loading-card">Загружаем ваши события…</div>}
          {!isAccountLoading && organizerEvents.length === 0 && !showCreateForm && (
            <div className="empty-list spacious">
              <span>✦</span>
              <h3>Создайте первое событие</h3>
              <p>Опишите встречу, укажите место и время — дальше его проверит модератор.</p>
              <button className="primary-button" type="button" onClick={openCreate}>
                Создать событие
              </button>
            </div>
          )}
          <div className="organizer-list">
            {organizerEvents.map((event) => (
              <article className="organizer-card" key={event.id}>
                <div>
                  <span className={'status-pill ' + event.status}>
                    {STATUS_LABELS[event.status] || event.status}
                  </span>
                  <h2>{event.title}</h2>
                  <p>{formatDate(event.start_time)} · {event.address}</p>
                </div>
                <div className="organizer-card-actions">
                  <span>{event.registered_count || 0} / {event.max_participants} участников</span>
                  {['pending', 'approved'].includes(event.status) && (
                    <button
                      className="text-button danger"
                      type="button"
                      onClick={() => handleCancelEvent(event.id)}
                      disabled={isActionBusy}
                    >
                      Отменить
                    </button>
                  )}
                </div>
              </article>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
