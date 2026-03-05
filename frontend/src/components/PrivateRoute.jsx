import { Navigate } from "react-router-dom";

/**
 * PrivateRoute — protects routes that require authentication.
 * requireOnboarded: also requires user to have completed onboarding.
 */
export default function PrivateRoute({ children, requireOnboarded = false }) {
    const token = localStorage.getItem("token");
    const user = JSON.parse(localStorage.getItem("user") || "{}");

    if (!token) {
        return <Navigate to="/auth" replace />;
    }

    if (requireOnboarded && !user.is_onboarded) {
        return <Navigate to="/onboarding" replace />;
    }

    return children;
}
