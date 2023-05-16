// follow up questions when the user check the hotels
document.getElementById("preferred-hotel").addEventListener("change", function() {
  if (this.value === "Hilton Hotel") {
    document.getElementById("follow-up-hotel-questions").style.display = "block";
  } else {
    document.getElementById("follow-up-hotel-questions").style.display = "none";
  }
});

// follow up questions when the user check the other payment
const otherPaymentCheckbox = document.querySelector('#other');
const otherPaymentQuestion = document.querySelector('#follow-up-payment-questions');

otherPaymentCheckbox.addEventListener('change', function() {
  if (otherPaymentCheckbox.checked) {
    otherPaymentQuestion.style.display = 'block';
  } else {
    otherPaymentQuestion.style.display = 'none';
  }
});

// validation before submission
document.getElementById("survey-form").addEventListener("submit", function(event) {
  if (!this.checkValidity()) {
    event.preventDefault();
  }
});


