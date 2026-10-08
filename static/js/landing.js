// landing.js — "See how it works" video modal

(function () {
    const modal = document.getElementById("video-modal");
    if (!modal) return;

    const iframe = document.getElementById("video-modal-iframe");
    const closeBtn = modal.querySelector("[data-video-close]");
    let lastFocused = null;

    function openModal(event) {
        event.preventDefault();
        lastFocused = document.activeElement;

        // Load the video only when opened, so it never plays in the background
        iframe.src = iframe.dataset.src;
        modal.hidden = false;
        document.body.style.overflow = "hidden";
        closeBtn.focus();
    }

    function closeModal() {
        if (modal.hidden) return;

        // Clearing src unloads the player, which stops playback
        iframe.removeAttribute("src");
        modal.hidden = true;
        document.body.style.overflow = "";
        if (lastFocused) lastFocused.focus();
    }

    document.querySelectorAll("[data-video-open]").forEach(function (trigger) {
        trigger.addEventListener("click", openModal);
    });

    closeBtn.addEventListener("click", closeModal);

    // Clicking the dark overlay (outside the dialog) closes the modal
    modal.addEventListener("click", function (event) {
        if (event.target === modal) closeModal();
    });

    document.addEventListener("keydown", function (event) {
        if (event.key === "Escape") closeModal();
    });
})();
