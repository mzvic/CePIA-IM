module Demo {
    interface Clock {
        void tick(string date);
    };

    interface Alarm {
        void ring(string message);
    };
};
