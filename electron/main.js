/**
 * main.js — Electron desktop wrapper for School Management System
 *
 * Install:   npm install electron
 * Run:       electron .  (after starting Django server)
 * Package:   npm install electron-builder
 *            npm run dist
 */

const { app, BrowserWindow, Menu, shell, dialog } = require('electron');
const { spawn } = require('child_process');
const path = require('path');
const http = require('http');

const PORT = 8765;
const SERVER_URL = `http://127.0.0.1:${PORT}`;
let mainWindow;
let djangoProcess;

// ── Start Django server ───────────────────────────────────────
function startDjangoServer() {
    const python = process.platform === 'win32' ? 'python' : 'python3';
    const manage  = path.join(__dirname, 'manage.py');

    djangoProcess = spawn(python, [manage, 'runserver', `127.0.0.1:${PORT}`, '--noreload'], {
        cwd: __dirname,
        env: { ...process.env, DJANGO_SETTINGS_MODULE: 'school_mgmt.settings' },
    });

    djangoProcess.stdout.on('data', d => console.log('[Django]', d.toString()));
    djangoProcess.stderr.on('data', d => console.error('[Django]', d.toString()));
    djangoProcess.on('close', code => console.log('[Django] exited with code', code));
}

// ── Wait for Django to be ready ───────────────────────────────
function waitForServer(url, retries = 30) {
    return new Promise((resolve, reject) => {
        const tryConnect = (n) => {
            if (n <= 0) return reject(new Error('Server not ready'));
            http.get(url, () => resolve()).on('error', () => {
                setTimeout(() => tryConnect(n - 1), 500);
            });
        };
        tryConnect(retries);
    });
}

// ── Create main window ────────────────────────────────────────
function createWindow() {
    mainWindow = new BrowserWindow({
        width: 1400,
        height: 900,
        minWidth: 900,
        minHeight: 600,
        title: 'School Management System',
        icon: path.join(__dirname, 'static', 'img', 'icon.png'),
        webPreferences: {
            nodeIntegration: false,
            contextIsolation: true,
        },
        show: false,
    });

    mainWindow.loadURL(SERVER_URL);

    mainWindow.once('ready-to-show', () => {
        mainWindow.show();
        mainWindow.maximize();
    });

    mainWindow.webContents.setWindowOpenHandler(({ url }) => {
        if (url.startsWith('http')) shell.openExternal(url);
        return { action: 'deny' };
    });

    // Application menu
    const menu = Menu.buildFromTemplate([
        {
            label: 'File',
            submenu: [
                { label: 'Dashboard', click: () => mainWindow.loadURL(SERVER_URL + '/dashboard/') },
                { type: 'separator' },
                { label: 'Quit', accelerator: 'CmdOrCtrl+Q', click: () => app.quit() },
            ]
        },
        {
            label: 'Students',
            submenu: [
                { label: 'All Students',     click: () => mainWindow.loadURL(SERVER_URL + '/students/') },
                { label: 'Register Student', click: () => mainWindow.loadURL(SERVER_URL + '/students/register/') },
            ]
        },
        {
            label: 'Fees',
            submenu: [
                { label: 'Fees Overview',   click: () => mainWindow.loadURL(SERVER_URL + '/fees/') },
                { label: 'Record Payment',  click: () => mainWindow.loadURL(SERVER_URL + '/fees/pay/') },
                { label: 'Defaulters',      click: () => mainWindow.loadURL(SERVER_URL + '/fees/defaulters/') },
            ]
        },
        {
            label: 'Academics',
            submenu: [
                { label: 'Exams',          click: () => mainWindow.loadURL(SERVER_URL + '/results/') },
                { label: 'Create Exam',    click: () => mainWindow.loadURL(SERVER_URL + '/results/create/') },
            ]
        },
        {
            label: 'Reports',
            submenu: [
                { label: 'All Reports',    click: () => mainWindow.loadURL(SERVER_URL + '/reports/') },
                { label: 'Enrollment',     click: () => mainWindow.loadURL(SERVER_URL + '/reports/enrollment/') },
                { label: 'Fees Report',    click: () => mainWindow.loadURL(SERVER_URL + '/reports/fees/') },
                { label: 'Academic',       click: () => mainWindow.loadURL(SERVER_URL + '/reports/academic/') },
            ]
        },
        {
            label: 'Settings',
            submenu: [
                { label: 'School Settings', click: () => mainWindow.loadURL(SERVER_URL + '/dashboard/settings/') },
                { label: 'Manage Users',    click: () => mainWindow.loadURL(SERVER_URL + '/auth/users/') },
                { label: 'Django Admin',    click: () => mainWindow.loadURL(SERVER_URL + '/admin/') },
            ]
        },
        {
            label: 'View',
            submenu: [
                { role: 'reload' },
                { role: 'forceReload' },
                { role: 'toggleDevTools' },
                { type: 'separator' },
                { role: 'resetZoom' },
                { role: 'zoomIn' },
                { role: 'zoomOut' },
                { type: 'separator' },
                { role: 'togglefullscreen' },
            ]
        }
    ]);
    Menu.setApplicationMenu(menu);
}

// ── App lifecycle ─────────────────────────────────────────────
app.whenReady().then(async () => {
    startDjangoServer();
    try {
        await waitForServer(SERVER_URL);
        createWindow();
    } catch (e) {
        dialog.showErrorBox('Startup Error', 'Could not start the server. Make sure Python and Django are installed.');
        app.quit();
    }
});

app.on('window-all-closed', () => {
    if (djangoProcess) djangoProcess.kill();
    if (process.platform !== 'darwin') app.quit();
});

app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
});
