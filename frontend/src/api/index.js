import axios from "axios";
import store from "@/store";

// Authentication is cookie based: the browser sends the HttpOnly access token
// automatically, so there is no Authorization header to set here.
const axios_jwt = axios.create({ withCredentials: true });

// Add the CSRF header if a csrftoken cookie exists. Cookie authentication is
// protected against cross-site form posts by SameSite=Lax, so this is only used
// when the backend does set the cookie.
axios_jwt.interceptors.request.use(function(config) {
    const csrfToken = document.cookie
        .split('; ')
        .find(row => row.startsWith('csrftoken='))
        ?.split('=')[1];

    if (csrfToken) {
        config.headers['X-CSRFToken'] = csrfToken;
    }

    return config;
});

// A 401 means the access cookie is no longer valid. Try to refresh it once; if
// that fails the session is gone, so log out and send the user to the login page.
axios_jwt.interceptors.response.use(
    (response) => response,
    async (error) => {
        const config = error.config;

        if (error.response?.status === 401 && config && !config._retried && !config.url.includes('/token/')) {
            config._retried = true;
            try {
                await store.dispatch('refreshToken');
                return await axios_jwt.request(config);
            } catch {
                // refreshToken has already logged out and taken the reader to the login page,
                // with the page they were on as where to go back to once they have logged in
                // again. Doing that here as well would navigate twice, and the address of a
                // request is not the address of a page - /api/read/../type/ has no page to
                // show, so a second navigation there is a blank screen.
            }
        }

        return Promise.reject(error);
    }
);

export default axios_jwt
