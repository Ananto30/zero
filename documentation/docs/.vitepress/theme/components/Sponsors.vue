<script setup>

import sponsorsJson from "@theme/data/sponsor.json";

const platinumSponsors = sponsorsJson.platinum;
const goldSponsors = sponsorsJson.average;

</script>

<template>
    <h1 class="title">Platinum Sponsors</h1>
    <div class="sponsors">
        <a class="sponsor" v-for="sponsor in platinumSponsors" :key="sponsor.name" :href="sponsor.link" target="_blank">
            <img :src="sponsor.image" :alt="sponsor.name" />
        </a>
    </div>
    <h1 class="title">Gold Sponsors</h1>
    <div class="sponsors">
        <a class="sponsor" v-for="sponsor in goldSponsors" :key="sponsor.name" :href="sponsor.link" target="_blank">
            <img :src="sponsor.image" :alt="sponsor.name" />
        </a>
    </div>
</template>

<style scoped>
.title {
    font-size: 3rem;
    font-weight: bold;
    margin-top: 120px;
    margin-bottom: 60px;
    text-align: center;
}

.sponsors {
    display: flex;
    flex-wrap: wrap;
    justify-content: center;
    align-items: center;
    margin: 0 auto;
    max-width: 100%;
}

.sponsor {
    background-color: #f1f1f1;
    display: flex;
    justify-content: center;
    align-items: center;
    width: 100%;
    height: 100px;
    border-radius: 10px;
}

.sponsor img {
    max-width: 100%;
    height: auto;
    padding: 20px;
}

@media (min-width: 400px) {
    .sponsor {
        width: calc(50% - 20px);
        height: 100px;
        margin: 10px;
    }
}

@media (min-width: 768px) {
    .sponsor {
        width: calc(33.33% - 20px);
        height: 100px;
    }
}

@media (min-width: 992px) {
    .sponsor {
        width: calc(25% - 20px);
        height: 120px;
    }
    .sponsors {
        max-width: 1160px;
    }
}
</style>
