import React, { useEffect, useMemo, useState } from 'react';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
const DEFAULT_COORDS = { latitude: 57.153033, longitude: 65.534328 };
const CATEGORY_LABELS = {
  all: 'Все',
  sport: 'Спорт',
  education: 'Обучение',
  culture: 'Культура',
  party: 'Развлечения',
  volunteering: 'Волонтерство',
};

const formatDate = (value) =>
  new Date(value).toLocaleString('ru-RU', {
    dateStyle: 'medium',
    timeStyle: 'short',
  });

const getMaxInitData = () => {
  if (typeof window === 'undefined') {
    return null;
  }

  return window.Telegram?.WebApp?.initData || null;
};

const getEmptyForm = () => ({
  title: '',
  description: '',
  category: 'culture',
  address: '',
  latitude: DEFAULT_COORDS.latitude,
  longitude: DEFAULT_COORDS.longitude,
  start_time: new Date(Date.now() + 3600000).toISOString().slice(0, 16),
  end_time: new Date(Date.now() + 7200000).toISOString().slice(0, 16),
  max_participants: 20,
});

export default function App() {
  const [events, setEvents] = useState([]);
  const [selectedEvent, setSelectedEvent] = useState(null);
  const [currentUser, setCurrentUser] = useState(null);
  const [authToken, setAuthToken] = useState(
    typeof window !== 'undefined' ? localStorage.getItem('max_access_token') : null,
  );
  const [statusMessage, setStatusMessage] = useState('');
  const [isAuthenticating, setIsAuthenticating] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [filters, setFilters] = useState({
    category: 'all',
    freeOnly: false,
    todayOnly: false,
  });
  const [userLocation, setUserLocation] = useState(DEFAULT_COORDS);
  const [formData, setFormData] = useState(getEmptyForm());

  const fetchEvents = async (locationOverride = userLocation) => {
    try {
      const params = new URLSearchParams({
        lat: String(locationOverride.latitude),
        lon: String(locationOverride.longitude),
        radius: '25',
      });

      const response = await fetch(`${API_BASE_URL}/api/v1/events/?${params.toString()}`);
      if (!response.ok) {
        return;
      }

      const data = await response.json();
      if (Array.isArray(data) && data.length > 0) {
        setEvents(data);
        setSelectedEvent((prev) => prev || data[0]);
      } else {
        setEvents([]);
        setSelectedEvent(null);
      }
    } catch (error) {
      console.warn('Using empty list because backend is unavailable:', error);
      setEvents([]);
      setSelectedEvent(null);
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

  const handleLocate = () => {
    if (!navigator.geolocation) {
      setStatusMessage('Геолокация недоступна в этом браузере.');
      return;
    }

    navigator.geolocation.getCurrentPosition(
      (position) => {
        const nextCoords = {
          latitude: position.coords.latitude,
          longitude: position.coords.longitude,
        };
        setUserLocation(nextCoords);
        setFormData((prev) => ({ ...prev, latitude: nextCoords.latitude, longitude: nextCoords.longitude }));
        fetchEvents(nextCoords);
        setStatusMessage('Геолокация обновлена. Список событий пересчитан.');
      },
      () => {
        setStatusMessage('Не удалось определить местоположение. Используется центр Тюмени.');
      },
      { enableHighAccuracy: true, timeout: 10000 },
    );
  };

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

  const handleCreateEvent = async (event) => {
    event.preventDefault();
    if (!authToken) {
      setStatusMessage('Для создания события нужна авторизация через MAX.');
      return;
    }

    setIsSubmitting(true);
    try {
      const payload = {
        ...formData,
        start_time: new Date(formData.start_time).toISOString(),
        end_time: new Date(formData.end_time).toISOString(),
        max_participants: Number(formData.max_participants),
      };

      const response = await fetch(`${API_BASE_URL}/api/v1/events/`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${authToken}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      });

      const data = await response.json();
      if (!response.ok) {
        throw new Error(data?.detail || 'Не удалось создать событие');
      }

      setStatusMessage(`Событие отправлено на модерацию: ${data.message || 'ожидает одобрения'}`);
      setFormData(getEmptyForm());
      setShowCreateForm(false);
      await fetchEvents();
    } catch (error) {
      console.error(error);
      setStatusMessage(error.message || 'Не удалось создать событие.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const filteredEvents = useMemo(() => {
    const today = new Date();
    return events.filter((event) => {
      const matchesCategory =
        filters.category === 'all' || event.category === filters.category;
      const matchesFreeOnly = !filters.freeOnly || (event.available_seats || 0) > 0;
      const matchesToday =
        !filters.todayOnly ||
        new Date(event.start_time).toDateString() === today.toDateString();
      return matchesCategory && matchesFreeOnly && matchesToday;
    });
  }, [events, filters]);

  useEffect(() => {
    if (!filteredEvents.length) {
      return;
    }
    setSelectedEvent((prev) => prev && filteredEvents.some((item) => item.id === prev.id) ? prev : filteredEvents[0]);
  }, [filteredEvents]);

  const stats = useMemo(
    () => ({
      total: filteredEvents.length,
      seats: filteredEvents.reduce((sum, event) => sum + (event.available_seats || 0), 0),
    }),
    [filteredEvents],
  );

  const mapPoints = useMemo(() => {
    const points = filteredEvents.length ? filteredEvents : events;
    if (!points.length) {
      return [];
    }

    const latitudes = points.map((point) => point.location?.latitude ?? point.latitude ?? DEFAULT_COORDS.latitude);
    const longitudes = points.map((point) => point.location?.longitude ?? point.longitude ?? DEFAULT_COORDS.longitude);
    const minLat = Math.min(...latitudes);
    const maxLat = Math.max(...latitudes);
    const minLon = Math.min(...longitudes);
    const maxLon = Math.max(...longitudes);

    return points.map((point) => {
      const lat = point.location?.latitude ?? point.latitude ?? DEFAULT_COORDS.latitude;
      const lon = point.location?.longitude ?? point.longitude ?? DEFAULT_COORDS.longitude;
      return {
        ...point,
        x: ((lon - minLon) / (maxLon - minLon || 1)) * 100,
        y: ((maxLat - lat) / (maxLat - minLat || 1)) * 100,
      };
    });
  }, [events, filteredEvents]);

  return (
    <div className="app-shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">MAX Mini App</p>
          <h1>Локатор Событий</h1>
        </div>
        <div className="topbar-actions">
          <button className="primary-button" type="button" onClick={handleLocate}>
            Где я?
          </button>
          <button
            className="secondary-button"
            type="button"
            onClick={() => setShowCreateForm((prev) => !prev)}
          >
            {showCreateForm ? 'Закрыть форму' : 'Создать событие'}
          </button>
          <small>
            {currentUser
              ? `Привет, ${currentUser.first_name || currentUser.username || 'MAX user'}`
              : isAuthenticating
                ? 'Авторизация...'
                : 'Локальный режим'}
          </small>
        </div>
      </header>

      {statusMessage && <div className="status-banner">{statusMessage}</div>}

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
          <strong>{userLocation ? 'До 25 км' : '5 км'}</strong>
        </div>
      </section>

      {showCreateForm && (
        <form className="event-form" onSubmit={handleCreateEvent}>
          <div className="form-grid">
            <label>
              Название
              <input value={formData.title} onChange={(e) => setFormData((prev) => ({ ...prev, title: e.target.value }))} required />
            </label>
            <label>
              Категория
              <select value={formData.category} onChange={(e) => setFormData((prev) => ({ ...prev, category: e.target.value }))}>
                {Object.entries(CATEGORY_LABELS)
                  .filter(([key]) => key !== 'all')
                  .map(([key, label]) => (
                    <option key={key} value={key}>{label}</option>
                  ))}
              </select>
            </label>
            <label className="full-width">
              Описание
              <textarea value={formData.description} onChange={(e) => setFormData((prev) => ({ ...prev, description: e.target.value }))} required rows="3" />
            </label>
            <label className="full-width">
              Адрес
              <input value={formData.address} onChange={(e) => setFormData((prev) => ({ ...prev, address: e.target.value }))} required />
            </label>
            <label>
              Широта
              <input type="number" step="0.000001" value={formData.latitude} onChange={(e) => setFormData((prev) => ({ ...prev, latitude: Number(e.target.value) }))} required />
            </label>
            <label>
              Долгота
              <input type="number" step="0.000001" value={formData.longitude} onChange={(e) => setFormData((prev) => ({ ...prev, longitude: Number(e.target.value) }))} required />
            </label>
            <label>
              Дата и время начала
              <input type="datetime-local" value={formData.start_time} onChange={(e) => setFormData((prev) => ({ ...prev, start_time: e.target.value }))} required />
            </label>
            <label>
              Дата и время конца
              <input type="datetime-local" value={formData.end_time} onChange={(e) => setFormData((prev) => ({ ...prev, end_time: e.target.value }))} required />
            </label>
            <label>
              Лимит участников
              <input type="number" min="1" value={formData.max_participants} onChange={(e) => setFormData((prev) => ({ ...prev, max_participants: Number(e.target.value) }))} required />
            </label>
          </div>
          <button className="primary-button" type="submit" disabled={isSubmitting}>
            {isSubmitting ? 'Отправляем...' : 'Опубликовать событие'}
          </button>
        </form>
      )}

      <main className="content-grid">
        <aside className="card-list">
          <div className="filter-row">
            {Object.entries(CATEGORY_LABELS).map(([key, label]) => (
              <button
                key={key}
                type="button"
                className={`filter-chip ${filters.category === key ? 'active' : ''}`}
                onClick={() => setFilters((prev) => ({ ...prev, category: key }))}
              >
                {label}
              </button>
            ))}
          </div>
          <label className="toggle-row">
            <input type="checkbox" checked={filters.freeOnly} onChange={() => setFilters((prev) => ({ ...prev, freeOnly: !prev.freeOnly }))} />
            Только бесплатные / свободные места
          </label>
          <label className="toggle-row">
            <input type="checkbox" checked={filters.todayOnly} onChange={() => setFilters((prev) => ({ ...prev, todayOnly: !prev.todayOnly }))} />
            Сегодня
          </label>

          <div className="map-panel">
            <div className="map-surface">
              {mapPoints.map((point) => (
                <button
                  key={point.id}
                  type="button"
                  className={`map-marker ${selectedEvent?.id === point.id ? 'selected' : ''}`}
                  style={{ left: `${point.x}%`, top: `${point.y}%` }}
                  onClick={() => setSelectedEvent(point)}
                  aria-label={point.title}
                  title={point.title}
                >
                  {point.available_seats || 0}
                </button>
              ))}
            </div>
          </div>

          {filteredEvents.length === 0 ? (
            <div className="empty-state">Нет событий по выбранным фильтрам.</div>
          ) : (
            filteredEvents.map((event) => (
              <button
                key={event.id}
                type="button"
                className={`event-card ${selectedEvent?.id === event.id ? 'selected' : ''}`}
                onClick={() => setSelectedEvent(event)}
              >
                <span className="tag">{CATEGORY_LABELS[event.category] || event.category}</span>
                <h3>{event.title}</h3>
                <p>{event.address}</p>
                <div className="meta-row">
                  <span>{formatDate(event.start_time)}</span>
                  <span>{event.available_seats} мест</span>
                </div>
              </button>
            ))
          )}
        </aside>

        <section className="detail-card">
          {selectedEvent ? (
            <>
              <div className="detail-header">
                <span className="tag">{CATEGORY_LABELS[selectedEvent.category] || selectedEvent.category}</span>
                <button
                  className="primary-button small"
                  type="button"
                  onClick={() => handleJoinEvent(selectedEvent.id)}
                  disabled={!authToken || (selectedEvent.available_seats || 0) <= 0}
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
