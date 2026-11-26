'use strict';

const state = {
  clients: [],
  trainings: [],
  bookings: [],
  memberships: [],
  viewClientId: null,
};

const $ = (selector) => document.querySelector(selector);

/* ---------- Утилиты ---------- */

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });

  if (response.status === 204) return null;

  let data = null;
  try {
    data = await response.json();
  } catch (error) {
    data = null;
  }

  if (!response.ok) {
    let message = 'Не получилось выполнить действие';
    if (data && data.detail) {
      if (typeof data.detail === 'string') {
        message = data.detail;
      } else if (Array.isArray(data.detail)) {
        const parts = data.detail.map((item) => item.msg).filter(Boolean);
        if (parts.length) message = parts.join('; ');
      }
    }
    throw new Error(message);
  }

  return data;
}

function toast(message, type = 'ok') {
  const box = document.createElement('div');
  box.className = 'toast' + (type === 'error' ? ' toast--error' : '');
  box.textContent = message;
  $('#toasts').appendChild(box);
  setTimeout(() => box.remove(), 4200);
}

const pad = (value) => String(value).padStart(2, '0');

function toDateInput(date) {
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`;
}

function toDateTimeInput(date) {
  return `${toDateInput(date)}T${pad(date.getHours())}:${pad(date.getMinutes())}`;
}

function formatDateTime(iso) {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return iso;
  return date.toLocaleString('ru-RU', {
    day: '2-digit',
    month: 'long',
    hour: '2-digit',
    minute: '2-digit',
  });
}

function formatDate(iso) {
  const date = new Date(`${iso}T00:00:00`);
  if (Number.isNaN(date.getTime())) return iso;
  return date.toLocaleDateString('ru-RU', { day: '2-digit', month: '2-digit', year: 'numeric' });
}

function plural(count, one, few, many) {
  const mod10 = count % 10;
  const mod100 = count % 100;
  if (mod10 === 1 && mod100 !== 11) return one;
  if (mod10 >= 2 && mod10 <= 4 && (mod100 < 12 || mod100 > 14)) return few;
  return many;
}

/* ---------- Отрисовка ---------- */

function fillSelect(select, items, placeholder, valueOf, labelOf) {
  const previous = select.value;
  select.innerHTML = '';

  if (!items.length) {
    const option = document.createElement('option');
    option.value = '';
    option.textContent = placeholder;
    option.disabled = true;
    option.selected = true;
    select.appendChild(option);
    return;
  }

  items.forEach((item) => {
    const option = document.createElement('option');
    option.value = valueOf(item);
    option.textContent = labelOf(item);
    select.appendChild(option);
  });

  if (previous && Array.from(select.options).some((option) => option.value === previous)) {
    select.value = previous;
  }
}

function cell(text, className) {
  const td = document.createElement('td');
  if (className) td.className = className;
  td.textContent = text;
  return td;
}

function renderSummary() {
  $('#sum-clients').textContent = state.clients.length;
  $('#sum-trainings').textContent = state.trainings.length;
  $('#sum-bookings').textContent = state.bookings.length;
  $('#clients-count').textContent = state.clients.length;
  $('#trainings-count').textContent = state.trainings.length;
  $('#bookings-count').textContent = state.bookings.length;
}

function renderClients() {
  const tbody = $('#clients-table tbody');
  tbody.innerHTML = '';

  state.clients.forEach((client, index) => {
    const row = document.createElement('tr');
    row.appendChild(cell(String(index + 1), 'muted'));
    row.appendChild(cell(client.full_name, 'strong'));
    row.appendChild(cell(client.phone, 'muted'));
    tbody.appendChild(row);
  });

  $('#clients-empty').hidden = state.clients.length > 0;
}

function renderTrainings() {
  const tbody = $('#trainings-table tbody');
  tbody.innerHTML = '';
  const now = new Date();

  state.trainings.forEach((training) => {
    const row = document.createElement('tr');
    row.appendChild(cell(training.title, 'strong'));
    row.appendChild(cell(formatDateTime(training.starts_at)));
    row.appendChild(cell(`${training.booked} из ${training.capacity}`, 'muted'));

    const stateCell = document.createElement('td');
    const pill = document.createElement('span');
    const started = new Date(training.starts_at) <= now;
    const full = training.booked >= training.capacity;

    if (started) {
      pill.className = 'pill pill--off';
      pill.textContent = 'Прошла';
    } else if (full) {
      pill.className = 'pill pill--warn';
      pill.textContent = 'Мест нет';
    } else {
      pill.className = 'pill pill--ok';
      pill.textContent = `Свободно ${training.capacity - training.booked}`;
    }

    stateCell.appendChild(pill);
    row.appendChild(stateCell);
    tbody.appendChild(row);
  });

  $('#trainings-empty').hidden = state.trainings.length > 0;
}

function renderBookings() {
  const tbody = $('#bookings-table tbody');
  tbody.innerHTML = '';

  state.bookings.forEach((booking) => {
    const row = document.createElement('tr');
    row.appendChild(cell(booking.client_name, 'strong'));
    row.appendChild(cell(booking.training_title));
    row.appendChild(cell(formatDateTime(booking.starts_at), 'muted'));

    const actionCell = document.createElement('td');
    const button = document.createElement('button');
    button.className = 'btn btn--ghost';
    button.type = 'button';
    button.textContent = 'Отменить';
    button.dataset.action = 'cancel';
    button.dataset.id = booking.id;
    actionCell.appendChild(button);
    row.appendChild(actionCell);

    tbody.appendChild(row);
  });

  $('#bookings-empty').hidden = state.bookings.length > 0;
}

function renderMemberships() {
  const tbody = $('#memberships-table tbody');
  tbody.innerHTML = '';
  const today = new Date();
  today.setHours(0, 0, 0, 0);

  state.memberships.forEach((membership) => {
    const row = document.createElement('tr');
    row.appendChild(
      cell(`${formatDate(membership.start_date)} — ${formatDate(membership.end_date)}`)
    );
    row.appendChild(
      cell(
        `${membership.visits_left} ${plural(membership.visits_left, 'посещение', 'посещения', 'посещений')}`,
        'strong'
      )
    );

    const start = new Date(`${membership.start_date}T00:00:00`);
    const end = new Date(`${membership.end_date}T00:00:00`);

    const statusCell = document.createElement('td');
    const pill = document.createElement('span');

    if (membership.visits_left <= 0) {
      pill.className = 'pill pill--warn';
      pill.textContent = 'Посещения закончились';
    } else if (today > end) {
      pill.className = 'pill pill--off';
      pill.textContent = 'Истёк';
    } else if (today < start) {
      pill.className = 'pill pill--warn';
      pill.textContent = 'Ещё не начался';
    } else {
      pill.className = 'pill pill--ok';
      pill.textContent = 'Действует';
    }

    statusCell.appendChild(pill);
    row.appendChild(statusCell);
    tbody.appendChild(row);
  });

  $('#memberships-empty').hidden = state.memberships.length > 0;
}

function render() {
  renderSummary();
  renderClients();
  renderTrainings();
  renderBookings();

  fillSelect(
    $('#membership-client'),
    state.clients,
    'Сначала добавьте клиента',
    (item) => item.id,
    (item) => `${item.full_name} · ${item.phone}`
  );

  fillSelect(
    $('#booking-client'),
    state.clients,
    'Сначала добавьте клиента',
    (item) => item.id,
    (item) => `${item.full_name} · ${item.phone}`
  );

  const now = new Date();
  const upcoming = state.trainings.filter((training) => new Date(training.starts_at) > now);

  fillSelect(
    $('#booking-training'),
    upcoming,
    'Нет предстоящих тренировок',
    (item) => item.id,
    (item) => `${item.title} — ${formatDateTime(item.starts_at)} (свободно ${item.capacity - item.booked})`
  );

  fillSelect(
    $('#membership-view-client'),
    state.clients,
    'Нет клиентов',
    (item) => item.id,
    (item) => item.full_name
  );

  if (state.viewClientId) {
    $('#membership-view-client').value = String(state.viewClientId);
  }

  renderMemberships();
}

/* ---------- Данные ---------- */

async function loadAll() {
  const [clients, trainings, bookings] = await Promise.all([
    api('/clients'),
    api('/trainings'),
    api('/bookings'),
  ]);

  state.clients = clients;
  state.trainings = trainings;
  state.bookings = bookings;

  render();
  await loadMemberships();
}

async function loadMemberships() {
  const select = $('#membership-view-client');
  const selected = Number(select.value || 0);
  const valid = state.clients.some((client) => client.id === selected);

  state.viewClientId = valid ? selected : state.clients.length ? state.clients[0].id : null;

  if (!state.viewClientId) {
    state.memberships = [];
    renderMemberships();
    return;
  }

  select.value = String(state.viewClientId);
  state.memberships = await api(`/clients/${state.viewClientId}/memberships`);
  renderMemberships();
}

/* ---------- События ---------- */

function bindTabs() {
  $('#tabs').addEventListener('click', (event) => {
    const tab = event.target.closest('.tab');
    if (!tab) return;

    document.querySelectorAll('.tab').forEach((item) => item.classList.remove('is-active'));
    tab.classList.add('is-active');

    document.querySelectorAll('.panel').forEach((panel) => {
      const isTarget = panel.id === `panel-${tab.dataset.tab}`;
      panel.hidden = !isTarget;
      panel.classList.toggle('is-active', isTarget);
    });
  });
}

function bindForms() {
  $('#client-form').addEventListener('submit', async (event) => {
    event.preventDefault();
    const form = event.target;
    const data = new FormData(form);

    try {
      await api('/clients', {
        method: 'POST',
        body: JSON.stringify({
          full_name: String(data.get('full_name')).trim(),
          phone: String(data.get('phone')).trim(),
        }),
      });
      form.reset();
      toast('Клиент добавлен');
      await loadAll();
    } catch (error) {
      toast(error.message, 'error');
    }
  });

  $('#membership-form').addEventListener('submit', async (event) => {
    event.preventDefault();
    const form = event.target;
    const data = new FormData(form);
    const clientId = Number(data.get('client_id'));

    if (!clientId) {
      toast('Сначала добавьте клиента', 'error');
      return;
    }

    try {
      await api(`/clients/${clientId}/memberships`, {
        method: 'POST',
        body: JSON.stringify({
          start_date: data.get('start_date'),
          end_date: data.get('end_date'),
          visits_total: Number(data.get('visits_total')),
        }),
      });
      toast('Абонемент оформлен');
      state.viewClientId = clientId;
      await loadAll();
    } catch (error) {
      toast(error.message, 'error');
    }
  });

  $('#training-form').addEventListener('submit', async (event) => {
    event.preventDefault();
    const form = event.target;
    const data = new FormData(form);
    const startsAt = String(data.get('starts_at'));

    try {
      await api('/trainings', {
        method: 'POST',
        body: JSON.stringify({
          title: String(data.get('title')).trim(),
          starts_at: startsAt.length === 16 ? `${startsAt}:00` : startsAt,
          capacity: Number(data.get('capacity')),
        }),
      });
      form.reset();
      applyDefaults();
      toast('Тренировка добавлена в расписание');
      await loadAll();
    } catch (error) {
      toast(error.message, 'error');
    }
  });

  $('#booking-form').addEventListener('submit', async (event) => {
    event.preventDefault();
    const data = new FormData(event.target);
    const trainingId = Number(data.get('training_id'));
    const clientId = Number(data.get('client_id'));

    if (!trainingId || !clientId) {
      toast('Нужны тренировка и клиент', 'error');
      return;
    }

    try {
      await api(`/trainings/${trainingId}/bookings`, {
        method: 'POST',
        body: JSON.stringify({ client_id: clientId }),
      });
      toast('Клиент записан на тренировку');
      await loadAll();
    } catch (error) {
      toast(error.message, 'error');
    }
  });

  $('#membership-view-client').addEventListener('change', async () => {
    try {
      await loadMemberships();
    } catch (error) {
      toast(error.message, 'error');
    }
  });

  $('#bookings-table').addEventListener('click', async (event) => {
    const button = event.target.closest('[data-action="cancel"]');
    if (!button) return;

    try {
      await api(`/bookings/${button.dataset.id}`, { method: 'DELETE' });
      toast('Запись отменена, посещение вернулось');
      await loadAll();
    } catch (error) {
      toast(error.message, 'error');
    }
  });
}

function applyDefaults() {
  const today = new Date();
  const inMonth = new Date();
  inMonth.setDate(inMonth.getDate() + 30);
  const tomorrow = new Date();
  tomorrow.setDate(tomorrow.getDate() + 1);
  tomorrow.setHours(18, 0, 0, 0);

  $('#membership-start').value = toDateInput(today);
  $('#membership-end').value = toDateInput(inMonth);
  $('#training-start').value = toDateTimeInput(tomorrow);
}

async function init() {
  applyDefaults();
  bindTabs();
  bindForms();

  try {
    await loadAll();
  } catch (error) {
    toast(`Не удалось загрузить данные: ${error.message}`, 'error');
  }
}

init();
