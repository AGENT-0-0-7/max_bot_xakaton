import React, { useEffect, useMemo, useState } from 'react';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

const DEFAULT_EVENTS = [
  {
    id: 1,
    title: 'IT-Лекторий: Архитектура Microservices',
    description: 'Лекция про микросервисы и production architecture.',
    address: 'ул. Перекопская, 155, Тюмень',
    category: 'education',
    start_time: '2026-10-15T18:00:00Z',
    max_participants: 40,
    available_seats: 18,
    location: { latitude: 57.1554, longitude: 65.5241 },
  },
  {
    id: 2,
    title: 'Турнир по настольному теннису',
    description: 'Открытый турнир для студентов и жителей района.',
    address: 'Спортивный комплекс, Тюмень',
    category: 'sport',
    start_time: '2026-10-16T15:00:00Z',
    max_participants: 20,
    available_seats: 11,
    location: { latitude: 57.1501, longitude: 65.5482 },
  },
];

const formatDate = (value) => new Date(value).toLocaleString('ru-RU', {
  dateStyle: 'medium',
  timeStyle: 'short',
});

const getMaxInitData = () => {
  if (typeof window === 'undefined') {
    return null;
  }

  return window.Telegram?.WebApp?.initData || null;
};

export default function App() {
  const [events, setEvents] = useState(DEFAULT_EVENTS);
  const [selectedEvent, setSelectedEvent] = useState(DEFAULT_EVENTS[0]);
  const [currentUser, setCurrentUser] = useState(null);
  const [authToken, setAuthToken] = useState(
    typeof window !== 'undefined' ? localStorage.getItem('max_access_token') : null,
  );
  const [statusMessage, setStatusMessage] = useState('');
  const [isAuthenticating, setIsAuthenticating] = useState(false);

  const fetchEvents = async () => {
    try {
      const response = await fetch(
        `${API_BASE_URL}/api/v1/events/?lat=57.153033&lon=65.534328&radius=10`,
      );
      if (!response.ok) {
        return;
      }

      const data = await response.json();
      if (Array.isArray(data) && data.length > 0) {
        setEvents(data);
        setSelectedEvent((prev) => prev || data[0]);
      }
    } catch (error) {
      console.warn('Using default demo events because backend is unavailable:', error);
    }
  };

  useEffect(() => {
    fetchEvents();
  }, []);

  useEffect(() => {
    const bootstrapMaxAuth = async () => {
      const initData = getMaxInitData();
      if (!initData) {
        return;
      }

      setIsAuthenticating(true);
      try {
        const response = await fetch(`${API_BASE_URL}/api/v1/auth/max/`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ init_data: initData }),
        });

        const data = await response.json();
        if (!response.ok) {
          throw new Error(data?.error || 'Не удалось войти через MAX');
        }

        setCurrentUser(data.user);
        setAuthToken(data.access_token);
        localStorage.setItem('max_access_token', data.access_token);
        setStatusMessage(`Вы вошли как ${data.user?.first_name || 'MAX user'}`);
      } catch (error) {
        console.warn('MAX auth failed:', error);
        setStatusMessage('MAX auth недоступен, показан локальный режим');
      } finally {
        setIsAuthenticating(false);
      }
    };

    bootstrapMaxAuth();
  }, []);

  const handleJoinEvent = async (eventId) => {
    if (!authToken) {
      setStatusMessage('Сначала войдите через MAX, чтобы записаться на событие.');
      return;
    }

    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/events/${eventId}/register/`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${authToken}`,
          'Content-Type': 'application/json',
        },
      });

      const data = await response.json();
      setStatusMessage(data.message || data.detail || 'Запись обновлена');
      await fetchEvents();
    } catch (error) {
      console.error('Registration failed:', error);
      setStatusMessage('Не удалось записаться на событие. Попробуйте позже.');
    }
  };

  const stats = useMemo(() => ({
    total: events.length,
    seats: events.reduce((sum, event) => sum + (event.available_seats || 0), 0),
  }), [events]);

  return (
    <div className="app-shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">MAX Mini App</p>
          <h1>Локатор Событий</h1>
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 6 }}>
          <button className="primary-button">Найти досуг</button>
          <small>{currentUser ? `Привет, ${currentUser.first_name || currentUser.username || 'MAX user'}` : isAuthenticating ? 'Авторизация...' : 'Локальный режим'}</small>
        </div>
      </header>

      {statusMessage && (
        <div className="status-banner" style={{ marginTop: 12, padding: '10px 14px', borderRadius: 10, background: '#f3f4f6' }}>
          {statusMessage}
        </div>
      )}

      <section className="stats-row">
        <div className="stat-card">
          <span>Активных событий</span>
          <strong>{stats.total}</strong>
        </div>
        <div className="stat-card">
          <span>Свободных мест</span>
          <strong>{stats.seats}</strong>
        </div>
        <div className="stat-card">
          <span>Рядом с тобой</span>
          <strong>5 км</strong>
        </div>
      </section>

      <main className="content-grid">
        <aside className="card-list">
          {events.map((event) => (
            <button
              key={event.id}
              type="button"
              className={`event-card ${selectedEvent?.id === event.id ? 'selected' : ''}`}
              onClick={() => setSelectedEvent(event)}
            >
              <span className="tag">{event.category}</span>
              <h3>{event.title}</h3>
              <p>{event.address}</p>
              <div className="meta-row">
                <span>{formatDate(event.start_time)}</span>
                <span>{event.available_seats} мест</span>
              </div>
            </button>
          ))}
        </aside>

        <section className="detail-card">
          {selectedEvent ? (
            <>
              <div className="detail-header">
                <span className="tag">{selectedEvent.category}</span>
                <button
                  className="primary-button small"
                  onClick={() => handleJoinEvent(selectedEvent.id)}
                  disabled={!authToken}
                >
                  {authToken ? 'Пойду' : 'Войти через MAX'}
                </button>
              </div>
              <h2>{selectedEvent.title}</h2>
              <p>{selectedEvent.description}</p>

              <div className="detail-grid">
                <div>
                  <label>Адрес</label>
                  <strong>{selectedEvent.address}</strong>
                </div>
                <div>
                  <label>Когда</label>
                  <strong>{formatDate(selectedEvent.start_time)}</strong>
                </div>
                <div>
                  <label>Лимит</label>
                  <strong>{selectedEvent.max_participants} участников</strong>
                </div>
                <div>
                  <label>Свободно</label>
                  <strong>{selectedEvent.available_seats} мест</strong>
                </div>
              </div>
            </>
          ) : (
            <p>Событий не найдено.</p>
          )}
        </section>
      </main>
    </div>
  );
}
