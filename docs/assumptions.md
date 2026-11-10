# Working assumptions

- The socket programming requirement will use authenticated WebSockets through Django Channels. A raw Python socket client will demonstrate the connection.
- A withdrawn application cannot be resubmitted because the student/posting pair is unique across all statuses.
- Selected is terminal; students cannot withdraw after selection.
- After approval, substantive listing edits require a new officer review; the owning employer may still close a posting.
