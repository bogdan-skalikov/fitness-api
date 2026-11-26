/*
 * Демо-режим для GitHub Pages: сервера нет, данные живут в памяти браузера.
 * Подменяет window.fetch, повторяя те же правила, что и backend в app/services.py.
 */
(function () {
  'use strict';

  const pad = (n) => String(n).padStart(2, '0');
  const localDate = (d) => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
  const localDateTime = (d) =>
    `${localDate(d)}T${pad(d.getHours())}:${pad(d.getMinutes())}:00`;

  function shift(dayOffset, hour, minute) {
    const d = new Date();
    d.setDate(d.getDate() + dayOffset);
    d.setHours(hour || 0, minute || 0, 0, 0);
    return d;
  }

  const state = {
    clients: [],
    memberships: [],
    trainings: [],
    bookings: [],
    seq: { clients: 0, memberships: 0, trainings: 0, bookings: 0 },
  };

  const nextId = (key) => (state.seq[key] += 1);

  /* --- Начальные данные --- */

  function seed() {
    state.clients = [
      { id: nextId('clients'), full_name: 'Анна Смирнова', phone: '+7 900 111-22-33' },
      { id: nextId('clients'), full_name: 'Игорь Волков', phone: '+7 900 222-33-44' },
      { id: nextId('clients'), full_name: 'Мария Ковалёва', phone: '+7 900 333-44-55' },
    ];

    state.memberships = [
      {
        id: nextId('memberships'),
        client_id: 1,
        start_date: localDate(shift(-5)),
        end_date: localDate(shift(30)),
        visits_left: 8,
      },
      {
        id: nextId('memberships'),
        client_id: 2,
        start_date: localDate(shift(-60)),
        end_date: localDate(shift(-10)),
        visits_left: 3,
      },
      {
        id: nextId('memberships'),
        client_id: 3,
        start_date: localDate(shift(-20)),
        end_date: localDate(shift(40)),
        visits_left: 0,
      },
    ];

    state.trainings = [
      { id: nextId('trainings'), title: 'Йога', starts_at: localDateTime(shift(1, 18, 0)), capacity: 10 },
      { id: nextId('trainings'), title: 'Пилатес', starts_at: localDateTime(shift(2, 19, 30)), capacity: 2 },
      { id: nextId('trainings'), title: 'Кроссфит', starts_at: localDateTime(shift(-1, 10, 0)), capacity: 12 },
    ];

    state.bookings = [
      { id: nextId('bookings'), client_id: 1, training_id: 1 },
      { id: nextId('bookings'), client_id: 2, training_id: 2 },
    ];
    state.memberships.find((m) => m.id === 1).visits_left -= 1;
    state.memberships.find((m) => m.id === 2).visits_left -= 1;
  }

  /* --- Правила --- */

  const findClient = (id) => state.clients.find((c) => c.id === Number(id));
  const findTraining = (id) => state.trainings.find((t) => t.id === Number(id));
  const findBooking = (id) => state.bookings.find((b) => b.id === Number(id));

  const bookingsFor = (trainingId) =>
    state.bookings.filter((b) => b.training_id === Number(trainingId)).length;

  function currentMembership(clientId, day) {
    return state.memberships
      .filter(
        (m) => m.client_id === Number(clientId) && m.start_date <= day && m.end_date >= day
      )
      .sort((a, b) => (a.end_date < b.end_date ? -1 : 1))[0];
  }

  function trainingOut(training) {
    return {
      id: training.id,
      title: training.title,
      starts_at: training.starts_at,
      capacity: training.capacity,
      booked: bookingsFor(training.id),
    };
  }

  function book(trainingId, clientId) {
    const training = findTraining(trainingId);
    if (!training) return { status: 404, data: { detail: 'Тренировка не найдена' } };

    const client = findClient(clientId);
    if (!client) return { status: 404, data: { detail: 'Клиент не найден' } };

    const now = new Date();
    const starts = new Date(training.starts_at);
    if (starts <= now) {
      return {
        status: 400,
        data: { detail: 'Нельзя записаться на тренировку, которая уже началась' },
      };
    }

    const duplicate = state.bookings.find(
      (b) => b.training_id === training.id && b.client_id === client.id
    );
    if (duplicate) {
      return { status: 409, data: { detail: 'Клиент уже записан на эту тренировку' } };
    }

    if (bookingsFor(training.id) >= training.capacity) {
      return { status: 409, data: { detail: 'На тренировке нет свободных мест' } };
    }

    const membership = currentMembership(client.id, localDate(now));
    if (!membership || membership.visits_left <= 0) {
      return {
        status: 403,
        data: { detail: 'Нет действующего абонемента с остатком посещений' },
      };
    }

    membership.visits_left -= 1;
    const booking = { id: nextId('bookings'), client_id: client.id, training_id: training.id };
    state.bookings.push(booking);
    return { status: 201, data: booking };
  }

  /* --- Маршрутизация --- */

  function route(method, path, body) {
    const url = path.replace(/^\/+/, '').replace(/\/+$/, '');
    const parts = url ? url.split('/') : [];
    const [resource, first, second] = parts;

    if (method === 'GET' && resource === 'health') return { status: 200, data: { status: 'ok' } };

    if (resource === 'clients' && !first) {
      if (method === 'GET') return { status: 200, data: state.clients };

      if (method === 'POST') {
        const fullName = String(body.full_name || '').trim();
        const phone = String(body.phone || '').trim();
        if (fullName.length < 2) {
          return { status: 422, data: { detail: 'ФИО слишком короткое' } };
        }
        if (state.clients.some((c) => c.phone === phone)) {
          return { status: 409, data: { detail: 'Клиент с таким телефоном уже существует' } };
        }
        const client = { id: nextId('clients'), full_name: fullName, phone };
        state.clients.push(client);
        return { status: 201, data: client };
      }
    }

    if (resource === 'clients' && first) {
      const client = findClient(first);
      if (!client) return { status: 404, data: { detail: 'Клиент не найден' } };

      if (!second && method === 'GET') return { status: 200, data: client };

      if (second === 'memberships') {
        if (method === 'GET') {
          return { status: 200, data: state.memberships.filter((m) => m.client_id === client.id) };
        }
        if (method === 'POST') {
          if (body.end_date < body.start_date) {
            return {
              status: 422,
              data: { detail: 'Дата окончания абонемента раньше даты начала' },
            };
          }
          const membership = {
            id: nextId('memberships'),
            client_id: client.id,
            start_date: body.start_date,
            end_date: body.end_date,
            visits_left: Number(body.visits_total),
          };
          state.memberships.push(membership);
          return { status: 201, data: membership };
        }
      }
    }

    if (resource === 'trainings') {
      if (!first) {
        if (method === 'GET') {
          return { status: 200, data: state.trainings.slice().sort((a, b) => (a.starts_at < b.starts_at ? -1 : 1)).map(trainingOut) };
        }
        if (method === 'POST') {
          const training = {
            id: nextId('trainings'),
            title: String(body.title || '').trim(),
            starts_at: body.starts_at,
            capacity: Number(body.capacity),
          };
          state.trainings.push(training);
          return { status: 201, data: trainingOut(training) };
        }
      }
      if (first && second === 'bookings' && method === 'POST') {
        return book(first, body.client_id);
      }
    }

    if (resource === 'bookings') {
      if (!first && method === 'GET') {
        const rows = state.bookings.map((b) => {
          const client = findClient(b.client_id) || { full_name: '—' };
          const training = findTraining(b.training_id) || { title: '—', starts_at: '' };
          return {
            id: b.id,
            client_id: b.client_id,
            client_name: client.full_name,
            training_id: b.training_id,
            training_title: training.title,
            starts_at: training.starts_at,
          };
        });
        return { status: 200, data: rows };
      }

      if (first && method === 'DELETE') {
        const booking = findBooking(first);
        if (!booking) return { status: 404, data: { detail: 'Запись не найдена' } };

        const membership = currentMembership(booking.client_id, localDate(new Date()));
        if (membership) membership.visits_left += 1;

        state.bookings = state.bookings.filter((b) => b.id !== booking.id);
        return { status: 204, data: null };
      }
    }

    return { status: 404, data: { detail: 'Не найдено' } };
  }

  /* --- Подмена fetch --- */

  seed();

  const realFetch = window.fetch.bind(window);

  window.fetch = function (input, init) {
    const url = typeof input === 'string' ? input : input.url;
    if (!url.startsWith('/')) return realFetch(input, init);

    const method = ((init && init.method) || 'GET').toUpperCase();
    let body = null;
    if (init && init.body) {
      try {
        body = JSON.parse(init.body);
      } catch (error) {
        body = null;
      }
    }

    const result = route(method, url, body || {});

    if (result.status === 204) {
      return Promise.resolve(new Response(null, { status: 204 }));
    }

    return Promise.resolve(
      new Response(JSON.stringify(result.data), {
        status: result.status,
        headers: { 'Content-Type': 'application/json' },
      })
    );
  };
})();
