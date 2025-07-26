<script setup>
import { useData } from "vitepress";
import sponsorsJson from "@theme/data/sponsor.json";

const { frontmatter } = useData();

const sponsors = sponsorsJson.platinum;

</script>

<template>
    <div v-if="frontmatter.sponsors !== false">
        <a v-for="sponsor in sponsors" :key="sponsor.name" :href="sponsor.link" target="_blank">
            <img class="img" :src="sponsor.image" :alt="sponsor.name" />
        </a>

        <a class="b-sponsor" href="https://www.buymeacoffee.com/ananto30" target="_blank">
            <p>Become Sponsor</p>
        </a>
    </div>
</template>

<style>
.img {
    margin-top: 4px;
    margin-bottom: px;
}

.b-sponsor {
    font-size: 16px;
    padding: 10px;
    font-weight: normal;
    text-align: center;
}

.b-sponsor:hover {
    text-decoration: underline;
    color: blueviolet;
}
</style>
